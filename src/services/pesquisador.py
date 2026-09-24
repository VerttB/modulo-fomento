from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Pesquisador


def listar_pesquisador(db: Session) -> list[Pesquisador]:
    return list(db.scalars(select(Pesquisador)))


def obter_pesquisador(db: Session, resource_id: int) -> Pesquisador:
    recurso = db.get(Pesquisador, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Pesquisador não encontrado(a).")
    return recurso


def criar_pesquisador(db: Session, payload: BaseModel) -> Pesquisador:
    recurso = Pesquisador(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_pesquisador(db: Session, resource_id: int, payload: BaseModel) -> Pesquisador:
    recurso = obter_pesquisador(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_pesquisador(db: Session, resource_id: int) -> None:
    recurso = obter_pesquisador(db, resource_id)
    db.delete(recurso)
    db.commit()

