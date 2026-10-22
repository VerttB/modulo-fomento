import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.ingest import IngestResponse
from src.use_cases.v1.ingest.execute import ingest_v1

router = APIRouter(tags=["Ingestão"])
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse, status_code=201)
def ingest(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestResponse:
    nome_arquivo = arquivo.filename or "arquivo-sem-nome"
    logger.info("Rota de ingestão acionada: arquivo=%s", nome_arquivo)
    response = ingest_v1(db, nome_arquivo, arquivo.file)
    logger.info("Rota de ingestão concluída: arquivo=%s lote=%s", nome_arquivo, response.ingestao_id)
    return response
