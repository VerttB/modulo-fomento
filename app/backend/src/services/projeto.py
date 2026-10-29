from typing import Any
from math import ceil
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import AreaConhecimento, Projeto
from src.services.privacidade import sanitizar_texto_livre
from src.services.busca import construir_busca


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_projeto(
    db: Session,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    termo: str | None = None,
) -> tuple[list[Projeto], int]:
    query = select(Projeto).order_by(Projeto.id)
    if termo and termo.strip():
        query = (
            query.outerjoin(Projeto.area_conhecimento)
            .where(construir_busca(termo, Projeto.busca, AreaConhecimento.termo))
        )
    return _paginar(db, query, page, size)


def obter_projeto(db: Session, resource_id: UUID) -> Projeto:
    recurso = db.get(Projeto, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Projeto não encontrado(a).")
    return recurso


def criar_projeto(db: Session, payload: BaseModel) -> Projeto:
    dados = payload.model_dump()
    dados["nome"] = sanitizar_texto_livre(dados.get("nome"))
    dados["resumo"] = sanitizar_texto_livre(dados.get("resumo"))
    if dados.get("area_conhecimento_id") is not None and db.get(
        AreaConhecimento, dados["area_conhecimento_id"]
    ) is None:
        raise ResourceNotFoundError("Área de conhecimento não encontrada.")
    recurso = Projeto(**dados)
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_projeto(db: Session, resource_id: UUID, payload: BaseModel) -> Projeto:
    recurso = obter_projeto(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo in ("nome", "resumo"):
        if campo in dados:
            dados[campo] = sanitizar_texto_livre(dados[campo])
    area_id = dados.get("area_conhecimento_id")
    if area_id is not None and db.get(AreaConhecimento, area_id) is None:
        raise ResourceNotFoundError("Área de conhecimento não encontrada.")
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_projeto(db: Session, resource_id: UUID) -> None:
    recurso = obter_projeto(db, resource_id)
    db.delete(recurso)
    db.commit()

