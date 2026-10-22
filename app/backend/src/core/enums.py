from enum import Enum


class AreaConhecimentoTipo(str, Enum):
    GRANDE_AREA = "grande_area"
    AREA = "area"
    SUBAREA = "subarea"


class PesquisadorStatus(str, Enum):
    APROVADO = "APROVADO"
    PENDENTE = "PENDENTE"
    REJEITADO = "REJEITADO"


class BolsaStatus(str, Enum):
    REGULAR = "REGULAR"
    PENDENTE_REVISAO = "PENDENTE_REVISAO"
    RESOLVIDA = "RESOLVIDA"
    DESCARTADA = "DESCARTADA"


class BolsaConflitoStatus(str, Enum):
    PENDENTE = "PENDENTE"
    RESOLVIDO = "RESOLVIDO"
    DESCARTADO = "DESCARTADO"


class IngestaoStatus(str, Enum):
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDA = "CONCLUIDA"
    FALHA = "FALHA"


class IngestaoLinhaStatus(str, Enum):
    PENDENTE = "PENDENTE"
    INSERIDA = "INSERIDA"
    INSERIDA_CONFLITO = "INSERIDA_CONFLITO"
    DUPLICADA = "DUPLICADA"
    IGNORADA = "IGNORADA"
    INVALIDA = "INVALIDA"
    ERRO = "ERRO"


class ModalidadeBolsa(str, Enum):
    IC = "IC"
    MESTRADO = "Mestrado"
    DOUTORADO = "Doutorado"
    POS_DOUTORADO = "Pós-Doutorado"
    TECNICO = "Técnico"
    OUTRA = "Outra"
