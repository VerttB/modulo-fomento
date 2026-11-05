from uuid import UUID

from pydantic import BaseModel


class AtualizacaoPesquisadoresResultado(BaseModel):
    consultados: int = 0
    atualizados: int = 0
    sem_resultado: int = 0
    alterados_concorrentemente: int = 0
    ultimo_id: UUID | None = None
    concluido: bool = False
    erro: str | None = None
