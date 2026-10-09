from typing import Any
from math import ceil

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Departamento, Unidade


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_unidade(db: Session, page: int = 1, size: int = DEFAULT_PAGE_SIZE) -> tuple[list[Unidade], int]:
    query = select(Unidade).order_by(Unidade.id)
    return _paginar(db, query, page, size)


def obter_unidade(db: Session, resource_id: int) -> Unidade:
    recurso = db.get(Unidade, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Unidade não encontrado(a).")
    return recurso


def _vincular_departamentos(db: Session, recurso: Unidade, ids: list[int]) -> None:
    recurso.departamentos = list(
        db.scalars(select(Departamento).where(Departamento.id.in_(ids)))
    ) if ids else []


def criar_unidade(db: Session, payload: BaseModel) -> Unidade:
    dados = payload.model_dump()
    departamento_ids = dados.pop("departamento_ids", [])
    recurso = Unidade(**dados)
    _vincular_departamentos(db, recurso, departamento_ids)
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_unidade(db: Session, resource_id: int, payload: BaseModel) -> Unidade:
    recurso = obter_unidade(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    departamento_ids = dados.pop("departamento_ids", None)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    if departamento_ids is not None:
        _vincular_departamentos(db, recurso, departamento_ids)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_unidade(db: Session, resource_id: int) -> None:
    recurso = obter_unidade(db, resource_id)
    db.delete(recurso)
    db.commit()

