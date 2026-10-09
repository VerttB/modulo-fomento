from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import DepartamentoCreate, DepartamentoRead, DepartamentoUpdate, PaginatedResponse
from src.services.departamento import (
    listar_departamento,
    obter_departamento,
    criar_departamento,
    atualizar_departamento,
    excluir_departamento,
)

router = APIRouter(prefix="/departamentos", tags=["Departamentos"])


@router.get("/", response_model=PaginatedResponse[DepartamentoRead])
def listar(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    db: Session = Depends(get_db),
):
    items, total = listar_departamento(db, page=page, size=size)
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/{resource_id}", response_model=DepartamentoRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_departamento(db, resource_id)


@router.post("/", response_model=DepartamentoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: DepartamentoCreate, db: Session = Depends(get_db)):
    return criar_departamento(db, payload)


@router.patch("/{resource_id}", response_model=DepartamentoRead)
def atualizar(resource_id: int, payload: DepartamentoUpdate, db: Session = Depends(get_db)):
    return atualizar_departamento(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_departamento(db, resource_id)
