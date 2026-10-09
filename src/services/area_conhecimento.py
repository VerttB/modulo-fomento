from typing import Any
from math import ceil

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.core.exceptions import DomainValidationError, ResourceNotFoundError
from src.models import AreaConhecimento


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_areas_conhecimento(db: Session, page: int = 1, size: int = DEFAULT_PAGE_SIZE) -> tuple[list[AreaConhecimento], int]:
    query = select(AreaConhecimento).order_by(AreaConhecimento.id)
    return _paginar(db, query, page, size)


def obter_area_conhecimento(db: Session, resource_id: int) -> AreaConhecimento:
    recurso = db.get(AreaConhecimento, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Área de conhecimento não encontrada.")
    return recurso


def _validar_pai(db: Session, tipo: str, pai_id: int | None) -> None:
    tipo_pai = {"grande_area": None, "area": "grande_area", "subarea": "area"}[tipo]
    if tipo_pai is None and pai_id is not None:
        raise DomainValidationError("Grande área não pode ter pai.")
    if tipo_pai is not None:
        pai = db.get(AreaConhecimento, pai_id) if pai_id is not None else None
        if pai is None or pai.tipo.value != tipo_pai:
            raise DomainValidationError(f"O pai de uma {tipo} deve ser do tipo {tipo_pai}.")


def criar_area_conhecimento(db: Session, payload: BaseModel) -> AreaConhecimento:
    dados = payload.model_dump()
    tipo = dados["tipo"].value
    _validar_pai(db, tipo, dados.get("pai_id"))
    recurso = AreaConhecimento(**dados)
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_area_conhecimento(db: Session, resource_id: int, payload: BaseModel) -> AreaConhecimento:
    recurso = obter_area_conhecimento(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    tipo = dados.get("tipo", recurso.tipo).value
    pai_id = dados.get("pai_id", recurso.pai_id)
    _validar_pai(db, tipo, pai_id)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_area_conhecimento(db: Session, resource_id: int) -> None:
    recurso = obter_area_conhecimento(db, resource_id)
    db.delete(recurso)
    db.commit()
