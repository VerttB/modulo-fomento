from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import DepartamentoCreate, DepartamentoRead, DepartamentoUpdate
from src.services.departamento import (
    listar_departamento,
    obter_departamento,
    criar_departamento,
    atualizar_departamento,
    excluir_departamento,
)

router = APIRouter(prefix="/departamentos", tags=["Departamentos"])


@router.get("/", response_model=list[DepartamentoRead])
def listar(db: Session = Depends(get_db)):
    return listar_departamento(db)


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
