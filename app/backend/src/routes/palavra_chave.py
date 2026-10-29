from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import (
    PalavraChaveCreate,
    PalavraChaveRead,
    PalavraChaveUpdate,
    ProjetoPalavrasChaveRead,
    ProjetoPalavrasChaveUpdate,
    PaginatedResponse,
)
from src.schemas.paginacao import PaginacaoQuery
from src.services.palavra_chave import (
    listar_palavras_chave,
    obter_palavra_chave,
    criar_palavra_chave,
    atualizar_palavra_chave,
    excluir_palavra_chave,
    listar_palavras_do_projeto,
    definir_palavras_do_projeto,
)

router = APIRouter(prefix="/palavras-chave", tags=["Palavras-chave"])


@router.get("/", response_model=PaginatedResponse[PalavraChaveRead])
def listar(
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_palavras_chave(
        db, page=paginacao.page, size=paginacao.size
    )
    pages = (total + paginacao.size - 1) // paginacao.size
    return PaginatedResponse(
        items=items, total=total, page=paginacao.page, size=paginacao.size, pages=pages
    )


@router.get("/{resource_id}", response_model=PalavraChaveRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_palavra_chave(db, resource_id)


@router.post("/", response_model=PalavraChaveRead, status_code=status.HTTP_201_CREATED)
def criar(payload: PalavraChaveCreate, db: Session = Depends(get_db)):
    return criar_palavra_chave(db, payload)


@router.patch("/{resource_id}", response_model=PalavraChaveRead)
def atualizar(resource_id: UUID, payload: PalavraChaveUpdate, db: Session = Depends(get_db)):
    return atualizar_palavra_chave(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_palavra_chave(db, resource_id)


@router.get("/projetos/{projeto_id}", response_model=ProjetoPalavrasChaveRead)
def listar_do_projeto(projeto_id: UUID, db: Session = Depends(get_db)):
    return listar_palavras_do_projeto(db, projeto_id)


@router.put("/projetos/{projeto_id}", response_model=ProjetoPalavrasChaveRead)
def definir_no_projeto(
    projeto_id: UUID,
    payload: ProjetoPalavrasChaveUpdate,
    db: Session = Depends(get_db),
):
    return definir_palavras_do_projeto(db, projeto_id, payload.palavras_chave_ids)
