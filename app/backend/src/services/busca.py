import re
from sqlalchemy import Text, cast, func, literal, literal_column, or_
from sqlalchemy.dialects.postgresql import TSQUERY

from src.core.exceptions import DomainValidationError
from src.core.search import PORTUGUESE_SEARCH_CONFIG


TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()]+')
OPERATORS = {"AND", "OR", "NOT"}


def _tokens(termo: str) -> list[str]:
    tokens = TOKEN.findall(termo.strip())
    if not tokens:
        return []
    # Sem operador, todo o texto é uma expressão contínua.
    if not any(token in OPERATORS for token in tokens):
        expression = termo.strip()
        if expression.startswith('"') and expression.endswith('"'):
            expression = expression[1:-1].replace('\\"', '"')
        return [expression]

    # Em uma expressão lógica, frases com espaços precisam de aspas.
    if any(
        not token.startswith('"')
        and token not in OPERATORS
        and token not in {"(", ")"}
        and any(char.isspace() for char in token)
        for token in tokens
    ):
        raise DomainValidationError("Use aspas para agrupar expressões com mais de uma palavra.")
    return tokens


class _Parser:
    def __init__(self, tokens: list[str], vector, area_column=None):
        self.tokens = tokens
        self.vector = vector
        self.area_column = area_column
        self.position = 0

    def parse(self):
        query = self._or()
        if self.position != len(self.tokens):
            raise DomainValidationError("Expressão de busca inválida. Verifique operadores e parênteses.")
        config = literal_column(f"'{PORTUGUESE_SEARCH_CONFIG}'::regconfig")
        matches = [self.vector.op("@@")(query)]
        if self.area_column is not None:
            area_vector = func.to_tsvector(config, func.coalesce(self.area_column, ""))
            matches.append(area_vector.op("@@")(query))
        return or_(*matches)

    def _or(self):
        expressions = [self._and()]
        while self._accept("OR"):
            expressions.append(self._and())
        return _combine(expressions, "||")

    def _and(self):
        expressions = [self._unary()]
        while self._accept("AND"):
            expressions.append(self._unary())
        return _combine(expressions, "&&")

    def _unary(self):
        if self._accept("NOT"):
            query = self._unary()
            config = literal_column(f"'{PORTUGUESE_SEARCH_CONFIG}'::regconfig")
            negated_query = literal("!(") + cast(query, Text) + literal(")")
            return func.to_tsquery(config, negated_query, type_=TSQUERY())
        if self._accept("("):
            expression = self._or()
            if not self._accept(")"):
                raise DomainValidationError("Falta fechar um parêntese na busca.")
            return expression
        if self.position >= len(self.tokens):
            raise DomainValidationError("A busca termina antes de completar a expressão.")
        token = self.tokens[self.position]
        if token in OPERATORS or token == ")":
            raise DomainValidationError("Expressão de busca inválida. Verifique operadores e parênteses.")
        self.position += 1
        value = token[1:-1].replace('\\"', '"') if token.startswith('"') else token
        if not value.strip():
            raise DomainValidationError("A busca contém uma expressão vazia.")
        config = literal_column(f"'{PORTUGUESE_SEARCH_CONFIG}'::regconfig")
        return func.phraseto_tsquery(config, value, type_=TSQUERY())

    def _accept(self, token: str) -> bool:
        if self.position < len(self.tokens) and self.tokens[self.position] == token:
            self.position += 1
            return True
        return False


def construir_busca(termo: str | None, vector, area_column=None):
    if not termo or not termo.strip() or vector is None:
        return None
    tokens = _tokens(termo)
    return _Parser(tokens, vector, area_column).parse()


def _combine(expressions, operator: str):
    combined = expressions[0]
    for expression in expressions[1:]:
        combined = combined.op(operator)(expression)
    return combined
