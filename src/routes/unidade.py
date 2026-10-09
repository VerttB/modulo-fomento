from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import UnidadeCreate, UnidadeRead, UnidadeUpdate, PaginatedResponse
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
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db),
):
    items, total = listar_unidade(db, page=page, size=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/{resource_id}", response_model=UnidadeRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_unidade(db, resource_id)


@router.post("/", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def criar(payload: UnidadeCreate, db: Session = Depends(get_db)):
    return criar_unidade(db, payload)


@router.patch("/{resource_id}", response_model=UnidadeRead)
def atualizar(resource_id: int, payload: UnidadeUpdate, db: Session = Depends(get_db)):
    return atualizar_unidade(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_unidade(db, resource_id)
