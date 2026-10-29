from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.enums import BolsaStatus
from src.schemas import BolsaCreate, BolsaRead, BolsaUpdate, PaginatedResponse, EstatisticasBolsas
from src.schemas.bolsa import BolsaFiltros, filtros_bolsa_query
from src.services.bolsa import (
    listar_bolsa,
    obter_bolsa,
    criar_bolsa,
    atualizar_bolsa,
    excluir_bolsa,
)
from src.use_cases.v1.reports.bolsas import relatorio_bolsas
from src.services.exportacao_bolsistas import (
    exportar_registros_bolsistas,
    exportar_resumo_bolsistas,
)

router = APIRouter(prefix="/bolsas", tags=["Bolsas"])
ACCEPT_DESCRIPTION = (
    "Formato: text/csv, application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet ou application/json."
)


@router.get("/exportar-resumo", response_class=StreamingResponse)
def exportar_resumo(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    recorte: list[Literal["territorio", "cidade", "instituicao"]] | None = Query(None),
    accept: Annotated[str | None, Header(description=ACCEPT_DESCRIPTION)] = None,
    db: Session = Depends(get_db),
):
    arquivo = exportar_resumo_bolsistas(
        db,
        filtros,
        recortes=recorte,
        accept=accept,
    )
    return StreamingResponse(
        arquivo.conteudo,
        media_type=arquivo.media_type,
        headers={"Content-Disposition": f'attachment; filename="{arquivo.filename}"'},
    )


@router.get("/", response_model=PaginatedResponse[BolsaRead])
def listar(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    status: BolsaStatus | None = Query(None, description="Filtrar pelo status da bolsa"),
    incluir_conflitos: bool = Query(False, description="Incluir bolsas em revisão de conflito"),
    termo: str | None = Query(None, max_length=150, description="Busca em pessoas, projetos, instituição e curso"),
    db: Session = Depends(get_db),
):
    items, total = listar_bolsa(
        db,
        page=page,
        size=size,
        **filtros.model_dump(),
        status=status,
        incluir_conflitos=incluir_conflitos,
        termo=termo,
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/exportar", response_class=StreamingResponse)
def exportar(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    termo: str | None = Query(None, max_length=150),
    accept: Annotated[str | None, Header(description=ACCEPT_DESCRIPTION)] = None,
    db: Session = Depends(get_db),
):
    arquivo = exportar_registros_bolsistas(
        db,
        filtros,
        termo=termo,
        accept=accept,
    )
    return StreamingResponse(
        arquivo.conteudo,
        media_type=arquivo.media_type,
        headers={"Content-Disposition": f'attachment; filename="{arquivo.filename}"'},
    )


@router.get("/estatisticas", response_model=EstatisticasBolsas)
def estatisticas(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    db: Session = Depends(get_db),
):
    return relatorio_bolsas(db, **filtros.model_dump())


@router.get("/{resource_id}", response_model=BolsaRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_bolsa(db, resource_id)


@router.post("/", response_model=BolsaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: BolsaCreate, db: Session = Depends(get_db)):
    return criar_bolsa(db, payload)


@router.patch("/{resource_id}", response_model=BolsaRead)
def atualizar(resource_id: UUID, payload: BolsaUpdate, db: Session = Depends(get_db)):
    return atualizar_bolsa(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_bolsa(db, resource_id)
