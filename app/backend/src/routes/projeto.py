from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import PaginatedResponse, ProjetoCreate, ProjetoRead, ProjetoUpdate
from src.schemas.paginacao import PaginacaoQuery
from src.services.projeto import (
    listar_projeto,
    obter_projeto,
    criar_projeto,
    atualizar_projeto,
    excluir_projeto,
)

router = APIRouter(prefix="/projetos", tags=["Projetos"])


@router.get("/", response_model=PaginatedResponse[ProjetoRead])
def listar(
    paginacao: PaginacaoQuery,
    termo: str | None = Query(None, max_length=150, description="Título, resumo ou área"),
    db: Session = Depends(get_db),
):
    items, total = listar_projeto(
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


@router.get("/{resource_id}", response_model=ProjetoRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_projeto(db, resource_id)


@router.post("/", response_model=ProjetoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: ProjetoCreate, db: Session = Depends(get_db)):
    return criar_projeto(db, payload)


@router.patch("/{resource_id}", response_model=ProjetoRead)
def atualizar(resource_id: UUID, payload: ProjetoUpdate, db: Session = Depends(get_db)):
    return atualizar_projeto(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_projeto(db, resource_id)
