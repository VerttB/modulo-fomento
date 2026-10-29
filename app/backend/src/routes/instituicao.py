from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import (
    BolsaInstituicaoRead,
    InstituicaoCreate,
    InstituicaoPerfilRead,
    InstituicaoRead,
    InstituicaoUpdate,
    PaginatedResponse,
    PesquisadorRead,
    ProjetoRead,
)
from src.schemas.paginacao import PaginacaoQuery
from src.services.instituicao import (
    listar_instituicao,
    obter_instituicao,
    criar_instituicao,
    atualizar_instituicao,
    excluir_instituicao,
    obter_perfil_instituicao,
    listar_pesquisadores_da_instituicao,
    listar_projetos_da_instituicao,
    listar_bolsas_da_instituicao,
)

router = APIRouter(prefix="/instituicoes", tags=["Instituições"])


@router.get("/", response_model=PaginatedResponse[InstituicaoRead])
def listar(
    paginacao: PaginacaoQuery,
    termo: str | None = Query(None, max_length=150),
    db: Session = Depends(get_db),
):
    items, total = listar_instituicao(
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


@router.get("/{resource_id}/perfil", response_model=InstituicaoPerfilRead)
def perfil(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_perfil_instituicao(db, resource_id)


@router.get("/{resource_id}/pesquisadores", response_model=PaginatedResponse[PesquisadorRead])
def pesquisadores(
    resource_id: UUID,
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_pesquisadores_da_instituicao(
        db, resource_id, paginacao.page, paginacao.size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=paginacao.page,
        size=paginacao.size,
        pages=(total + paginacao.size - 1) // paginacao.size,
    )


@router.get("/{resource_id}/projetos", response_model=PaginatedResponse[ProjetoRead])
def projetos(
    resource_id: UUID,
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_projetos_da_instituicao(
        db, resource_id, paginacao.page, paginacao.size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=paginacao.page,
        size=paginacao.size,
        pages=(total + paginacao.size - 1) // paginacao.size,
    )


@router.get("/{resource_id}/bolsas", response_model=PaginatedResponse[BolsaInstituicaoRead])
def bolsas(
    resource_id: UUID,
    paginacao: PaginacaoQuery,
    db: Session = Depends(get_db),
):
    items, total = listar_bolsas_da_instituicao(
        db, resource_id, paginacao.page, paginacao.size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=paginacao.page,
        size=paginacao.size,
        pages=(total + paginacao.size - 1) // paginacao.size,
    )


@router.get("/{resource_id}", response_model=InstituicaoRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_instituicao(db, resource_id)


@router.post("/", response_model=InstituicaoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: InstituicaoCreate, db: Session = Depends(get_db)):
    return criar_instituicao(db, payload)


@router.patch("/{resource_id}", response_model=InstituicaoRead)
def atualizar(resource_id: UUID, payload: InstituicaoUpdate, db: Session = Depends(get_db)):
    return atualizar_instituicao(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_instituicao(db, resource_id)
