from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from src.core.enums import AreaConhecimentoTipo


class ProjetoCreate(BaseModel):
    nome: str
    resumo: str
    grande_area: str
    subarea: str


class ProjetoUpdate(BaseModel):
    nome: str | None = None
    resumo: str | None = None
    grande_area: str | None = None
    subarea: str | None = None


class ProjetoRead(ProjetoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PesquisadorCreate(BaseModel):
    lattes: str
    nome: str


class PesquisadorUpdate(BaseModel):
    lattes: str | None = None
    nome: str | None = None


class PesquisadorRead(PesquisadorCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class InstituicaoCreate(BaseModel):
    nome: str
    cep: str
    sigla: str


class InstituicaoUpdate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    sigla: str | None = None


class InstituicaoRead(InstituicaoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DepartamentoCreate(BaseModel):
    nome: str
    unidade: str
    cep: str
    instituicao_id: int


class DepartamentoUpdate(BaseModel):
    nome: str | None = None
    unidade: str | None = None
    cep: str | None = None
    instituicao_id: int | None = None


class DepartamentoRead(DepartamentoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UnidadeCreate(BaseModel):
    nome: str
    cep: str
    departamento_id: int


class UnidadeUpdate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    departamento_id: int | None = None


class UnidadeRead(UnidadeCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class BolsaCreate(BaseModel):
    quando_iniciou: date
    quando_terminou: date | None = None
    data_saida_pesquisador: date | None = None
    modalidade: str
    nome_curso: str
    projeto_id: int
    instituicao_id: int
    pesquisador_id: int


class BolsaUpdate(BaseModel):
    quando_iniciou: date | None = None
    quando_terminou: date | None = None
    data_saida_pesquisador: date | None = None
    modalidade: str | None = None
    nome_curso: str | None = None
    projeto_id: int | None = None
    instituicao_id: int | None = None
    pesquisador_id: int | None = None


class BolsaRead(BolsaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PalavraChaveCreate(BaseModel):
    termo: str
    termo_normalizado: str


class PalavraChaveUpdate(BaseModel):
    termo: str | None = None
    termo_normalizado: str | None = None


class PalavraChaveRead(PalavraChaveCreate):
    id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjetoPalavrasChaveUpdate(BaseModel):
    palavras_chave_ids: list[int]


class ProjetoPalavrasChaveRead(BaseModel):
    projeto_id: int
    palavras_chave: list[PalavraChaveRead]
    model_config = ConfigDict(from_attributes=True)


class AreaConhecimentoCreate(BaseModel):
    termo: str
    termo_normalizado: str
    tipo: AreaConhecimentoTipo
    pai_id: int | None = None


class AreaConhecimentoUpdate(BaseModel):
    termo: str | None = None
    termo_normalizado: str | None = None
    tipo: AreaConhecimentoTipo | None = None
    pai_id: int | None = None


class AreaConhecimentoRead(AreaConhecimentoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
