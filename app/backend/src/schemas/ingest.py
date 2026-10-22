from pydantic import BaseModel, Field
from uuid import UUID


class IngestResponse(BaseModel):
    ingestao_id: UUID
    linhas_processadas: int
    linhas_duplicadas: int
    linhas_ignoradas: int = 0
    erros: list[str] = Field(default_factory=list)
    projetos_criados: int
    bolsas_criadas: int
    bolsas_conflitantes: int = 0
    pesquisadores_criados: int
    pesquisadores_atualizados: int
    pesquisadores_pendentes: int
    palavras_chave_criadas: int
    areas_criadas: int
