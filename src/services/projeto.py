from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Projeto


def listar_projeto(db: Session) -> list[Projeto]:
    return list(db.scalars(select(Projeto)))


def obter_projeto(db: Session, resource_id: int) -> Projeto:
    recurso = db.get(Projeto, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Projeto não encontrado(a).")
    return recurso


def criar_projeto(db: Session, payload: BaseModel) -> Projeto:
    recurso = Projeto(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_projeto(db: Session, resource_id: int, payload: BaseModel) -> Projeto:
    recurso = obter_projeto(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_projeto(db: Session, resource_id: int) -> None:
    recurso = obter_projeto(db, resource_id)
    db.delete(recurso)
    db.commit()

