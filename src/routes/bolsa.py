from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas import BolsaCreate, BolsaRead, BolsaUpdate
from src.services.bolsa import (
    listar_bolsa,
    obter_bolsa,
    criar_bolsa,
    atualizar_bolsa,
    excluir_bolsa,
)

router = APIRouter(prefix="/bolsas", tags=["Bolsas"])


@router.get("/", response_model=list[BolsaRead])
def listar(db: Session = Depends(get_db)):
    return listar_bolsa(db)


@router.get("/{resource_id}", response_model=BolsaRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_bolsa(db, resource_id)


@router.post("/", response_model=BolsaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: BolsaCreate, db: Session = Depends(get_db)):
    return criar_bolsa(db, payload)


@router.patch("/{resource_id}", response_model=BolsaRead)
def atualizar(resource_id: int, payload: BolsaUpdate, db: Session = Depends(get_db)):
    return atualizar_bolsa(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_bolsa(db, resource_id)
