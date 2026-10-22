from typing import Any
from math import ceil
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.core.enums import BolsaStatus
from src.models import Bolsa, Pesquisador


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_pesquisador(
    db: Session,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    termo: str | None = None,
) -> tuple[list[Pesquisador], int]:
    conditions = []
    if termo and termo.strip():
        pattern = f"%{termo.strip()}%"
        conditions.append(
            or_(
                Pesquisador.nome.ilike(pattern),
                Pesquisador.lattes.ilike(pattern),
                Pesquisador.cidade.ilike(pattern),
            )
        )
    cep_ultima_bolsa = (
        select(Bolsa.cep_referencia)
        .where(
            Bolsa.pesquisador_id == Pesquisador.id,
            Bolsa.status != BolsaStatus.DESCARTADA,
        )
        .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc())
        .limit(1)
        .scalar_subquery()
    )
    total = (
        db.scalar(
            select(func.count())
            .select_from(Pesquisador)
            .where(*conditions)
        )
        or 0
    )
    rows = db.execute(
        select(Pesquisador, cep_ultima_bolsa.label("cep_referencia"))
        .where(*conditions)
        .order_by(Pesquisador.id)
        .limit(size)
        .offset((page - 1) * size)
    ).all()
    items = []
    for researcher, cep in rows:
        researcher.cep_referencia = cep
        items.append(researcher)
    return items, total


def obter_pesquisador(db: Session, resource_id: UUID) -> Pesquisador:
    recurso = db.get(Pesquisador, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Pesquisador não encontrado(a).")
    recurso.cep_referencia = db.scalar(
        select(Bolsa.cep_referencia)
        .where(
            Bolsa.pesquisador_id == recurso.id,
            Bolsa.status != BolsaStatus.DESCARTADA,
        )
        .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc())
        .limit(1)
    )
    return recurso


def criar_pesquisador(db: Session, payload: BaseModel) -> Pesquisador:
    recurso = Pesquisador(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_pesquisador(db: Session, resource_id: UUID, payload: BaseModel) -> Pesquisador:
    recurso = obter_pesquisador(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_pesquisador(db: Session, resource_id: UUID) -> None:
    recurso = obter_pesquisador(db, resource_id)
    db.delete(recurso)
    db.commit()

