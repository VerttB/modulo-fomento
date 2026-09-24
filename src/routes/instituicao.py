from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import InstituicaoCreate, InstituicaoRead, InstituicaoUpdate
from src.services.instituicao import (
    listar_instituicao,
    obter_instituicao,
    criar_instituicao,
    atualizar_instituicao,
    excluir_instituicao,
)

router = APIRouter(prefix="/instituicoes", tags=["Instituições"])


@router.get("/", response_model=list[InstituicaoRead])
def listar(db: Session = Depends(get_db)):
    return listar_instituicao(db)


@router.get("/{resource_id}", response_model=InstituicaoRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_instituicao(db, resource_id)


@router.post("/", response_model=InstituicaoRead, status_code=status.HTTP_201_CREATED)
def criar(payload: InstituicaoCreate, db: Session = Depends(get_db)):
    return criar_instituicao(db, payload)


@router.patch("/{resource_id}", response_model=InstituicaoRead)
def atualizar(resource_id: int, payload: InstituicaoUpdate, db: Session = Depends(get_db)):
    return atualizar_instituicao(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_instituicao(db, resource_id)
