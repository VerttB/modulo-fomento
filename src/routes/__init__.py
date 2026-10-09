from fastapi import APIRouter

from src.routes.area_conhecimento import router as area_conhecimento_router
from src.routes.bolsa import router as bolsa_router
from src.routes.departamento import router as departamento_router
from src.routes.instituicao import router as instituicao_router
from src.routes.ingest import router as ingest_router
from src.routes.palavra_chave import router as palavra_chave_router
from src.routes.pesquisador import router as pesquisador_router
from src.routes.projeto import router as projeto_router
from src.routes.unidade import router as unidade_router

router = APIRouter()
router.include_router(projeto_router)
router.include_router(pesquisador_router)
router.include_router(bolsa_router)
router.include_router(instituicao_router)
router.include_router(departamento_router)
router.include_router(unidade_router)
router.include_router(area_conhecimento_router)
router.include_router(palavra_chave_router)
router.include_router(ingest_router)
