from datetime import date, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.core.enums import AreaConhecimentoTipo, ModalidadeBolsa, PesquisadorStatus


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ProjetoCreate(BaseModel):
    nome: str | None = None
    resumo: str | None = None
    grande_area: str | None = None
    subarea: str | None = None


class ProjetoUpdate(BaseModel):
    nome: str | None = None
    resumo: str | None = None
    grande_area: str | None = None
    subarea: str | None = None


class ProjetoRead(ProjetoCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class PesquisadorCreate(BaseModel):
    cpf: str | None = None
    lattes: str | None = None
    nome: str | None = None
    cidade: str | None = None
    status: PesquisadorStatus = PesquisadorStatus.PENDENTE


class PesquisadorUpdate(BaseModel):
    cpf: str | None = None
    lattes: str | None = None
    nome: str | None = None
    cidade: str | None = None
    status: PesquisadorStatus | None = None


class PesquisadorRead(PesquisadorCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class InstituicaoCreate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    sigla: str | None = None


class InstituicaoUpdate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    sigla: str | None = None


class InstituicaoRead(InstituicaoCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class DepartamentoCreate(BaseModel):
    nome: str | None = None
    unidade: str | None = None
    cep: str | None = None
    instituicao_id: UUID
    grande_area_id: UUID | None = None


class DepartamentoUpdate(BaseModel):
    nome: str | None = None
    unidade: str | None = None
    cep: str | None = None
    instituicao_id: UUID | None = None
    grande_area_id: UUID | None = None


class DepartamentoRead(DepartamentoCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class UnidadeCreate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    departamento_ids: list[UUID] = []


class UnidadeUpdate(BaseModel):
    nome: str | None = None
    cep: str | None = None
    departamento_ids: list[UUID] | None = None


class UnidadeRead(UnidadeCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class BolsaCreate(BaseModel):
    quando_iniciou: date | None = None
    quando_terminou: date | None = None
    data_saida_pesquisador: date | None = None
    modalidade: ModalidadeBolsa | None = None
    nome_curso: str | None = None
    projeto_id: UUID
    instituicao_id: UUID
    pesquisador_id: UUID


class BolsaUpdate(BaseModel):
    quando_iniciou: date | None = None
    quando_terminou: date | None = None
    data_saida_pesquisador: date | None = None
    modalidade: ModalidadeBolsa | None = None
    nome_curso: str | None = None
    projeto_id: UUID | None = None
    instituicao_id: UUID | None = None
    pesquisador_id: UUID | None = None


class BolsaRead(BolsaCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class PalavraChaveCreate(BaseModel):
    termo: str
    termo_normalizado: str


class PalavraChaveUpdate(BaseModel):
    termo: str | None = None
    termo_normalizado: str | None = None


class PalavraChaveRead(PalavraChaveCreate):
    id: UUID
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjetoPalavrasChaveUpdate(BaseModel):
    palavras_chave_ids: list[UUID]


class ProjetoPalavrasChaveRead(BaseModel):
    projeto_id: UUID
    palavras_chave: list[PalavraChaveRead]
    model_config = ConfigDict(from_attributes=True)


class AreaConhecimentoCreate(BaseModel):
    termo: str
    termo_normalizado: str
    tipo: AreaConhecimentoTipo
    pai_id: UUID | None = None


class AreaConhecimentoUpdate(BaseModel):
    termo: str | None = None
    termo_normalizado: str | None = None
    tipo: AreaConhecimentoTipo | None = None
    pai_id: UUID | None = None


class AreaConhecimentoRead(AreaConhecimentoCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class EstatisticasBolsas(BaseModel):
    total: int
    por_modalidade: dict[str, int]
    por_instituicao: list[dict[str, Any]]
    por_cidade: list[dict[str, Any]]
    por_grande_area: list[dict[str, Any]]
    por_area: list[dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)
