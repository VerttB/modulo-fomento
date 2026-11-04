import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.ingest import IngestaoRecebida
from src.use_cases.v1.ingest.execute import registrar_ingestao

router = APIRouter(tags=["Ingestão"])
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestaoRecebida, status_code=202)
def ingest(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestaoRecebida:
    nome_arquivo = arquivo.filename or "arquivo-sem-nome"
    logger.info("Rota de ingestão acionada")
    ingestao_id = registrar_ingestao(db, nome_arquivo, arquivo.file)
    logger.info("Arquivo recebido para ingestão: lote=%s", ingestao_id)
    return IngestaoRecebida(ingestao_id=ingestao_id)
