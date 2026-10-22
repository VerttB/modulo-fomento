from datetime import date, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.core.enums import (
    AreaConhecimentoTipo,
    BolsaConflitoStatus,
    BolsaStatus,
    IngestaoLinhaStatus,
    IngestaoStatus,
    PesquisadorStatus,
)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class TerritorioIdentidadeRead(BaseModel):
    id: UUID
    nome: str
    nome_normalizado: str
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


class ProjetoCreate(BaseModel):
    nome: str | None = None
    resumo: str | None = None
    area_conhecimento_id: UUID | None = None


class ProjetoUpdate(BaseModel):
    nome: str | None = None
    resumo: str | None = None
    area_conhecimento_id: UUID | None = None


class ProjetoRead(ProjetoCreate):
    id: UUID
    area_conhecimento: AreaConhecimentoRead | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("nome", "resumo")
    def serializar_texto_sem_dados_pessoais(self, valor: str | None) -> str | None:
        from src.services.privacidade import sanitizar_texto_livre

        return sanitizar_texto_livre(valor)


class PesquisadorCreate(BaseModel):
    lattes: str | None = None
    nome: str | None = None
    cidade: str | None = None
    territorio_identidade_id: UUID | None = None
    status: PesquisadorStatus = PesquisadorStatus.PENDENTE


class PesquisadorUpdate(BaseModel):
    lattes: str | None = None
    nome: str | None = None
    cidade: str | None = None
    territorio_identidade_id: UUID | None = None
    status: PesquisadorStatus | None = None


class PesquisadorRead(PesquisadorCreate):
    id: UUID
    cep_referencia: str | None = None
    territorio_identidade: TerritorioIdentidadeRead | None = None
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
    cep_referencia: str | None = None
    modalidade: str | None = None
    nome_curso: str | None = None
    projeto_id: UUID
    instituicao_id: UUID
    pesquisador_id: UUID


class BolsaUpdate(BaseModel):
    quando_iniciou: date | None = None
    quando_terminou: date | None = None
    data_saida_pesquisador: date | None = None
    cep_referencia: str | None = None
    modalidade: str | None = None
    nome_curso: str | None = None
    projeto_id: UUID | None = None
    instituicao_id: UUID | None = None
    pesquisador_id: UUID | None = None


class BolsaRead(BolsaCreate):
    id: UUID
    ingestao_id: UUID | None = None
    linha_origem: int | None = None
    is_conflict: bool
    status: BolsaStatus
    model_config = ConfigDict(from_attributes=True)


class IngestaoRead(BaseModel):
    id: UUID
    nome_arquivo: str
    quantidade_linhas: int
    tipo: str
    status: IngestaoStatus
    iniciada_em: datetime
    finalizada_em: datetime | None
    linhas_processadas: int
    linhas_duplicadas: int
    linhas_ignoradas: int
    bolsas_conflitantes: int
    pesquisadores_consultados: int
    pesquisadores_total: int
    model_config = ConfigDict(from_attributes=True)


class IngestaoBolsaConflitoRead(BaseModel):
    id: UUID
    status: BolsaConflitoStatus
    motivo: str
    bolsa_id: UUID
    modalidade: str | None
    quando_iniciou: date | None
    quando_terminou: date | None
    projeto_nome: str | None


class IngestaoLinhaRead(BaseModel):
    id: UUID
    linha_origem: int
    status: IngestaoLinhaStatus
    motivo: str | None
    linha_duplicada: int | None
    atualizada_em: datetime
    lattes_id: str | None
    pesquisador_id: UUID | None
    pesquisador_nome: str | None
    projeto_id: UUID | None
    projeto_nome: str | None
    bolsa_id: UUID | None
    modalidade: str | None
    quando_iniciou: date | None
    quando_terminou: date | None
    instituicao_nome: str | None
    bolsa_status: BolsaStatus | None
    is_conflict: bool | None
    bolsas_conflitantes: list[IngestaoBolsaConflitoRead] = Field(default_factory=list)


class IngestaoExecucaoRead(BaseModel):
    id: UUID
    numero: int
    status: IngestaoStatus
    iniciada_em: datetime
    finalizada_em: datetime | None
    erro: str | None
    model_config = ConfigDict(from_attributes=True)


class IngestaoLinhaEventoRead(BaseModel):
    id: UUID
    execucao_id: UUID
    execucao_numero: int | None = None
    status: IngestaoLinhaStatus
    motivo: str | None
    bolsa_id: UUID | None
    pesquisador_id: UUID | None
    projeto_id: UUID | None
    criado_em: datetime
    projeto_nome: str | None = None
    pesquisador_nome: str | None = None
    model_config = ConfigDict(from_attributes=True)


class IngestaoResumoRead(BaseModel):
    ingestao_id: UUID
    total_linhas: int
    por_status: dict[str, int]
    total_execucoes: int


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


class EstatisticasBolsas(BaseModel):
    total: int
    por_ano: list[dict[str, Any]]
    por_modalidade: dict[str, int]
    por_instituicao: list[dict[str, Any]]
    por_cidade: list[dict[str, Any]]
    por_territorio_identidade: list[dict[str, Any]]
    por_grande_area: list[dict[str, Any]]
    por_area: list[dict[str, Any]]
    por_subarea: list[dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)


class InstituicaoPerfilRead(BaseModel):
    instituicao: InstituicaoRead
    total_pesquisadores: int
    total_projetos: int
    estatisticas: EstatisticasBolsas


class BolsaInstituicaoRead(BaseModel):
    id: UUID
    quando_iniciou: date | None
    quando_terminou: date | None
    modalidade: str | None
    nome_curso: str | None
    status: BolsaStatus
    is_conflict: bool
    pesquisador_nome: str | None
    pesquisador_cidade: str | None
    projeto_nome: str | None
