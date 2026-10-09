from typing import Any
from math import ceil

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Instituicao


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_instituicao(db: Session, page: int = 1, size: int = DEFAULT_PAGE_SIZE) -> tuple[list[Instituicao], int]:
    query = select(Instituicao).order_by(Instituicao.id)
    return _paginar(db, query, page, size)


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

