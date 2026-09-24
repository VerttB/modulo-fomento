from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Departamento


def listar_departamento(db: Session) -> list[Departamento]:
    return list(db.scalars(select(Departamento)))


def obter_departamento(db: Session, resource_id: int) -> Departamento:
    recurso = db.get(Departamento, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Departamento não encontrado(a).")
    return recurso


def criar_departamento(db: Session, payload: BaseModel) -> Departamento:
    recurso = Departamento(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_departamento(db: Session, resource_id: int, payload: BaseModel) -> Departamento:
    recurso = obter_departamento(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_departamento(db: Session, resource_id: int) -> None:
    recurso = obter_departamento(db, resource_id)
    db.delete(recurso)
    db.commit()

