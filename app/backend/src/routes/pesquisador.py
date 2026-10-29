from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import PaginatedResponse, PesquisadorCreate, PesquisadorRead, PesquisadorUpdate
from src.schemas.paginacao import PaginacaoQuery
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
    paginacao: PaginacaoQuery,
    termo: str | None = Query(None, max_length=150, description="Nome, Lattes ou cidade"),
    db: Session = Depends(get_db),
):
    items, total = listar_pesquisador(
        db, page=paginacao.page, size=paginacao.size, termo=termo
    )
    pages = (total + paginacao.size - 1) // paginacao.size
    return PaginatedResponse(
        items=items,
        total=total,
        page=paginacao.page,
        size=paginacao.size,
        pages=pages,
    )


@router.get("/{resource_id}", response_model=PesquisadorRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_pesquisador(db, resource_id)


@router.post("/", response_model=PesquisadorRead, status_code=status.HTTP_201_CREATED)
def criar(payload: PesquisadorCreate, db: Session = Depends(get_db)):
    return criar_pesquisador(db, payload)


@router.patch("/{resource_id}", response_model=PesquisadorRead)
def atualizar(resource_id: UUID, payload: PesquisadorUpdate, db: Session = Depends(get_db)):
    return atualizar_pesquisador(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_pesquisador(db, resource_id)
