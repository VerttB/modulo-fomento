from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import PaginatedResponse, PesquisadorCreate, PesquisadorRead, PesquisadorUpdate
from src.services.pesquisador import (
    listar_pesquisador,
    obter_pesquisador,
    criar_pesquisador,
    atualizar_pesquisador,
    excluir_pesquisador,
)

router = APIRouter(prefix="/pesquisadores", tags=["Pesquisadores"])


@router.get("/", response_model=PaginatedResponse[PesquisadorRead])
def listar(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db),
):
    items, total = listar_pesquisador(db, page=page, size=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/{resource_id}", response_model=PesquisadorRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_pesquisador(db, resource_id)


@router.post("/", response_model=PesquisadorRead, status_code=status.HTTP_201_CREATED)
def criar(payload: PesquisadorCreate, db: Session = Depends(get_db)):
    return criar_pesquisador(db, payload)


@router.patch("/{resource_id}", response_model=PesquisadorRead)
def atualizar(resource_id: int, payload: PesquisadorUpdate, db: Session = Depends(get_db)):
    return atualizar_pesquisador(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_pesquisador(db, resource_id)
