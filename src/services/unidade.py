from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Unidade


def listar_unidade(db: Session) -> list[Unidade]:
    return list(db.scalars(select(Unidade)))


def obter_unidade(db: Session, resource_id: int) -> Unidade:
    recurso = db.get(Unidade, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Unidade não encontrado(a).")
    return recurso


def criar_unidade(db: Session, payload: BaseModel) -> Unidade:
    recurso = Unidade(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_unidade(db: Session, resource_id: int, payload: BaseModel) -> Unidade:
    recurso = obter_unidade(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_unidade(db: Session, resource_id: int) -> None:
    recurso = obter_unidade(db, resource_id)
    db.delete(recurso)
    db.commit()

