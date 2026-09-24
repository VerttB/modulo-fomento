from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import ProjetoCreate, ProjetoRead, ProjetoUpdate
from src.services.projeto import (
    listar_projeto,
    obter_projeto,
    criar_projeto,
    atualizar_projeto,
    excluir_projeto,
)

router = APIRouter(prefix="/projetos", tags=["Projetos"])


@router.get("/", response_model=list[ProjetoRead])
def listar(db: Session = Depends(get_db)):
    return listar_projeto(db)


@router.get("/{resource_id}", response_model=ProjetoRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_projeto(db, resource_id)


@router.post("/", response_model=ProjetoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: ProjetoCreate, db: Session = Depends(get_db)):
    return criar_projeto(db, payload)


@router.patch("/{resource_id}", response_model=ProjetoRead)
def atualizar(resource_id: int, payload: ProjetoUpdate, db: Session = Depends(get_db)):
    return atualizar_projeto(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_projeto(db, resource_id)
