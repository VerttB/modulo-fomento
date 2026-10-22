import re


_CPF_PATTERN = re.compile(
    r"(?<!\d)(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?!\d)"
)


def sanitizar_texto_livre(valor: str | None) -> str | None:
    if valor is None:
        return None
    return _CPF_PATTERN.sub("[CPF removido]", valor)
