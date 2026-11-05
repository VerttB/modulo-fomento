from uuid import UUID

from pydantic import BaseModel, Field


class AtualizacaoPesquisadoresRequest(BaseModel):
    apos_id: UUID | None = None
    tamanho_lote: int = Field(default=30, ge=1, le=100)


class AtualizacaoPesquisadoresResultado(BaseModel):
    consultados: int = 0
    atualizados: int = 0
    sem_resultado: int = 0
    alterados_concorrentemente: int = 0
    ultimo_id: UUID | None = None
    concluido: bool = False
    erro: str | None = None
