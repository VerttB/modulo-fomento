from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import AreaConhecimentoCreate, AreaConhecimentoRead, AreaConhecimentoUpdate, PaginatedResponse
from src.schemas.paginacao import PaginacaoQuery
from src.services.area_conhecimento import (
    listar_areas_conhecimento,
    obter_area_conhecimento,
    criar_area_conhecimento,
    atualizar_area_conhecimento,
    excluir_area_conhecimento,
)

router = APIRouter(prefix="/areas-conhecimento", tags=["Áreas de conhecimento"])


@router.get("/", response_model=PaginatedResponse[AreaConhecimentoRead])
def listar(
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_areas_conhecimento(
        db, page=paginacao.page, size=paginacao.size
    )
    pages = (total + paginacao.size - 1) // paginacao.size
    return PaginatedResponse(
        items=items, total=total, page=paginacao.page, size=paginacao.size, pages=pages
    )


@router.get("/{resource_id}", response_model=AreaConhecimentoRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_area_conhecimento(db, resource_id)


@router.post("/", response_model=AreaConhecimentoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: AreaConhecimentoCreate, db: Session = Depends(get_db)):
    return criar_area_conhecimento(db, payload)


@router.patch("/{resource_id}", response_model=AreaConhecimentoRead)
def atualizar(resource_id: UUID, payload: AreaConhecimentoUpdate, db: Session = Depends(get_db)):
    return atualizar_area_conhecimento(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_area_conhecimento(db, resource_id)
