from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import UnidadeCreate, UnidadeRead, UnidadeUpdate, PaginatedResponse
from src.schemas.paginacao import PaginacaoQuery
from src.services.unidade import (
    listar_unidade,
    obter_unidade,
    criar_unidade,
    atualizar_unidade,
    excluir_unidade,
)

router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.get("/", response_model=PaginatedResponse[UnidadeRead])
def listar(
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_unidade(db, page=paginacao.page, size=paginacao.size)
    pages = (total + paginacao.size - 1) // paginacao.size
    return PaginatedResponse(
        items=items, total=total, page=paginacao.page, size=paginacao.size, pages=pages
    )


@router.get("/{resource_id}", response_model=UnidadeRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_unidade(db, resource_id)


@router.post("/", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def criar(payload: UnidadeCreate, db: Session = Depends(get_db)):
    return criar_unidade(db, payload)


@router.patch("/{resource_id}", response_model=UnidadeRead)
def atualizar(resource_id: UUID, payload: UnidadeUpdate, db: Session = Depends(get_db)):
    return atualizar_unidade(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_unidade(db, resource_id)
