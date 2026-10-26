from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.enums import IngestaoLinhaStatus, IngestaoStatus
from src.core.exceptions import IngestFormatError
from src.services.ingest_files import caminho_seguro
from src.schemas import (
    IngestaoExecucaoRead,
    IngestaoLinhaEventoRead,
    IngestaoLinhaRead,
    IngestaoRead,
    IngestaoResumoRead,
    PaginatedResponse,
)
from src.services.ingestao import (
    listar_eventos_linha,
    listar_execucoes_ingestao,
    listar_ingestoes,
    listar_linhas_ingestao,
    obter_ingestao,
    resumo_ingestao,
)
from src.use_cases.v1.ingest.execute import retomar_ingestao
from src.use_cases.v1.ingest.rebuild_trace import reconstruir_rastreabilidade


router = APIRouter(prefix="/ingestoes", tags=["Ingestões"])


@router.get("/", response_model=PaginatedResponse[IngestaoRead])
def listar(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = listar_ingestoes(db, page, size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{ingestao_id}", response_model=IngestaoRead)
def obter(ingestao_id: UUID, db: Session = Depends(get_db)):
    return obter_ingestao(db, ingestao_id)


@router.get("/{ingestao_id}/resumo", response_model=IngestaoResumoRead)
def resumo(ingestao_id: UUID, db: Session = Depends(get_db)):
    return resumo_ingestao(db, ingestao_id)


@router.get("/{ingestao_id}/linhas", response_model=PaginatedResponse[IngestaoLinhaRead])
def listar_linhas(
    ingestao_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    status: IngestaoLinhaStatus | None = None,
    termo: str | None = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    items, total = listar_linhas_ingestao(
        db, ingestao_id, page, size, status, termo
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{ingestao_id}/execucoes", response_model=list[IngestaoExecucaoRead])
def listar_execucoes(ingestao_id: UUID, db: Session = Depends(get_db)):
    return listar_execucoes_ingestao(db, ingestao_id)


@router.get(
    "/{ingestao_id}/linhas/{linha_id}/eventos",
    response_model=list[IngestaoLinhaEventoRead],
)
def listar_eventos(
    ingestao_id: UUID, linha_id: UUID, db: Session = Depends(get_db)
):
    return listar_eventos_linha(db, ingestao_id, linha_id)


@router.post("/{ingestao_id}/retomar")
def retomar(ingestao_id: UUID, db: Session = Depends(get_db)):
    return retomar_ingestao(db, ingestao_id)


@router.post("/{ingestao_id}/rastreabilidade/reconstruir")
def reconstruir_linhas(ingestao_id: UUID, db: Session = Depends(get_db)):
    return reconstruir_rastreabilidade(db, ingestao_id)


@router.get("/{ingestao_id}/arquivo")
def baixar_arquivo_sanitizado(ingestao_id: UUID, db: Session = Depends(get_db)):
    ingestao = obter_ingestao(db, ingestao_id)
    if ingestao.status != IngestaoStatus.CONCLUIDA or not ingestao.arquivo_path:
        raise IngestFormatError("O arquivo sem CPF estará disponível após a conclusão da ingestão.")
    path = caminho_seguro(ingestao.arquivo_path)
    if not path.is_file():
        raise IngestFormatError("O arquivo sanitizado não está disponível no armazenamento.")
    return FileResponse(
        path,
        media_type="text/csv",
        filename=f"ingestao-{ingestao.id}-com-lattes.csv",
    )
