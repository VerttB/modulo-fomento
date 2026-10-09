from fastapi import APIRouter, Depends, Query, status
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
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db),
):
    items, total = listar_palavras_chave(db, page=page, size=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/{resource_id}", response_model=PalavraChaveRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_palavra_chave(db, resource_id)


@router.post("/", response_model=PalavraChaveRead, status_code=status.HTTP_201_CREATED)
def criar(payload: PalavraChaveCreate, db: Session = Depends(get_db)):
    return criar_palavra_chave(db, payload)


@router.patch("/{resource_id}", response_model=PalavraChaveRead)
def atualizar(resource_id: int, payload: PalavraChaveUpdate, db: Session = Depends(get_db)):
    return atualizar_palavra_chave(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_palavra_chave(db, resource_id)


@router.get("/projetos/{projeto_id}", response_model=ProjetoPalavrasChaveRead)
def listar_do_projeto(projeto_id: int, db: Session = Depends(get_db)):
    return listar_palavras_do_projeto(db, projeto_id)


@router.put("/projetos/{projeto_id}", response_model=ProjetoPalavrasChaveRead)
def definir_no_projeto(
    projeto_id: int,
    payload: ProjetoPalavrasChaveUpdate,
    db: Session = Depends(get_db),
):
    return definir_palavras_do_projeto(db, projeto_id, payload.palavras_chave_ids)
