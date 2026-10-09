from enum import Enum


class AreaConhecimentoTipo(str, Enum):
    GRANDE_AREA = "grande_area"
    AREA = "area"
    SUBAREA = "subarea"


class PesquisadorStatus(str, Enum):
    APROVADO = "APROVADO"
    PENDENTE = "PENDENTE"
    REJEITADO = "REJEITADO"


class ModalidadeBolsa(str, Enum):
    IC = "IC"
    MESTRADO = "Mestrado"
    DOUTORADO = "Doutorado"
    POS_DOUTORADO = "Pós-Doutorado"
    TECNICO = "Técnico"
    OUTRA = "Outra"
