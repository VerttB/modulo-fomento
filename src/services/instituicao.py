from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Instituicao


def listar_instituicao(db: Session) -> list[Instituicao]:
    return list(db.scalars(select(Instituicao)))


def obter_instituicao(db: Session, resource_id: int) -> Instituicao:
    recurso = db.get(Instituicao, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Instituição não encontrado(a).")
    return recurso


def criar_instituicao(db: Session, payload: BaseModel) -> Instituicao:
    recurso = Instituicao(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_instituicao(db: Session, resource_id: int, payload: BaseModel) -> Instituicao:
    recurso = obter_instituicao(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_instituicao(db: Session, resource_id: int) -> None:
    recurso = obter_instituicao(db, resource_id)
    db.delete(recurso)
    db.commit()

