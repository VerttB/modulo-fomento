from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Bolsa


def listar_bolsa(db: Session) -> list[Bolsa]:
    return list(db.scalars(select(Bolsa)))


def obter_bolsa(db: Session, resource_id: int) -> Bolsa:
    recurso = db.get(Bolsa, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Bolsa não encontrado(a).")
    return recurso


def criar_bolsa(db: Session, payload: BaseModel) -> Bolsa:
    recurso = Bolsa(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_bolsa(db: Session, resource_id: int, payload: BaseModel) -> Bolsa:
    recurso = obter_bolsa(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_bolsa(db: Session, resource_id: int) -> None:
    recurso = obter_bolsa(db, resource_id)
    db.delete(recurso)
    db.commit()

