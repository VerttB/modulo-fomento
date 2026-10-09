from pydantic import BaseModel


class IngestResponse(BaseModel):
    linhas_processadas: int
    linhas_duplicadas: int
    linhas_ignoradas: int = 0
    erros: list[str] = []
    projetos_criados: int
    bolsas_criadas: int
    pesquisadores_criados: int
    pesquisadores_atualizados: int
    pesquisadores_pendentes: int
    palavras_chave_criadas: int
    areas_criadas: int
