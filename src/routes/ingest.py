from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.ingest import IngestResponse
from src.services.ingest import ingerir_arquivo

router = APIRouter(tags=["Ingestão"])


@router.post("/ingest", response_model=IngestResponse, status_code=201)
def ingest(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestResponse:
    conteudo = arquivo.file.read()
    return ingerir_arquivo(db, arquivo.filename or "", conteudo)
