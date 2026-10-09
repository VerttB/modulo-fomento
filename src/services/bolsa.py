from typing import Any
from math import ceil
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.core.exceptions import ResourceNotFoundError
from src.models import Bolsa, Instituicao, Pesquisador, Projeto, AreaConhecimento


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_bolsa(
    db: Session,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    area: str | None = None,
    grande_area: str | None = None,
    universidade: str | None = None,
    cidade: str | None = None,
    modalidade: str | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
) -> tuple[list[Bolsa], int]:
    query = select(Bolsa).order_by(Bolsa.id)
    
    # Aplica filtros com joins necessários
    if any([area, grande_area]):
        query = query.join(Projeto, Bolsa.projeto_id == Projeto.id)
        if area:
            query = query.where(Projeto.subarea.ilike(f"%{area}%"))
        if grande_area:
            query = query.where(Projeto.grande_area.ilike(f"%{grande_area}%"))
    
    if universidade:
        query = query.join(Instituicao, Bolsa.instituicao_id == Instituicao.id)
        query = query.where(
            (Instituicao.nome.ilike(f"%{universidade}%")) | 
            (Instituicao.sigla.ilike(f"%{universidade}%"))
        )
    
    if cidade:
        query = query.join(Pesquisador, Bolsa.pesquisador_id == Pesquisador.id)
        query = query.where(Pesquisador.cidade.ilike(f"%{cidade}%"))
    
    if modalidade:
        query = query.where(Bolsa.modalidade.ilike(f"%{modalidade}%"))
    
    if ano_inicio:
        query = query.where(
            func.extract('year', Bolsa.quando_iniciou) >= ano_inicio
        )
    
    if ano_fim:
        query = query.where(
            func.extract('year', Bolsa.quando_iniciou) <= ano_fim
        )
    
    return _paginar(db, query, page, size)


def estatisticas_bolsas(db: Session) -> dict:
    """Retorna estatísticas gerais das bolsas."""
    total = db.scalar(select(func.count(Bolsa.id)))
    
    # Por modalidade
    por_modalidade = db.execute(
        select(Bolsa.modalidade, func.count(Bolsa.id))
        .group_by(Bolsa.modalidade)
    ).all()
    modalidades = {m: c for m, c in por_modalidade if m}
    
    # Por instituição
    por_instituicao = db.execute(
        select(Instituicao.nome, Instituicao.sigla, func.count(Bolsa.id))
        .join(Bolsa, Bolsa.instituicao_id == Instituicao.id)
        .group_by(Instituicao.id, Instituicao.nome, Instituicao.sigla)
        .order_by(func.count(Bolsa.id).desc())
    ).all()
    instituicoes = [
        {"nome": n, "sigla": s, "total": c} for n, s, c in por_instituicao
    ]
    
    # Por cidade (do pesquisador)
    por_cidade = db.execute(
        select(Pesquisador.cidade, func.count(Bolsa.id))
        .join(Bolsa, Bolsa.pesquisador_id == Pesquisador.id)
        .where(Pesquisador.cidade.is_not(None))
        .group_by(Pesquisador.cidade)
        .order_by(func.count(Bolsa.id).desc())
    ).all()
    cidades = [{"cidade": c, "total": t} for c, t in por_cidade if c]
    
    # Por grande área e área (via projeto)
    por_grande_area = db.execute(
        select(Projeto.grande_area, func.count(Bolsa.id))
        .join(Bolsa, Bolsa.projeto_id == Projeto.id)
        .where(Projeto.grande_area.is_not(None))
        .group_by(Projeto.grande_area)
        .order_by(func.count(Bolsa.id).desc())
    ).all()
    grandes_areas = [{"grande_area": g, "total": t} for g, t in por_grande_area if g]
    
    por_area = db.execute(
        select(Projeto.grande_area, Projeto.subarea, func.count(Bolsa.id))
        .join(Bolsa, Bolsa.projeto_id == Projeto.id)
        .where(Projeto.subarea.is_not(None))
        .group_by(Projeto.grande_area, Projeto.subarea)
        .order_by(func.count(Bolsa.id).desc())
    ).all()
    areas = [
        {"grande_area": g, "area": a, "total": t} for g, a, t in por_area if a
    ]
    
    return {
        "total": total or 0,
        "por_modalidade": modalidades,
        "por_instituicao": instituicoes,
        "por_cidade": cidades,
        "por_grande_area": grandes_areas,
        "por_area": areas,
    }


def obter_bolsa(db: Session, resource_id: int) -> Bolsa:
    recurso = db.get(Bolsa, resource_id)
    if recurso is None:
        raise ResourceNotFoundError("Bolsa não encontrado(a).")
    return recurso


def criar_bolsa(db: Session, payload: BaseModel) -> Bolsa:
    recurso = Bolsa(**payload.model_dump())
    db.add(recurso)
    db.commit()
    db.refresh(recurso)
    return recurso


def atualizar_bolsa(db: Session, resource_id: int, payload: BaseModel) -> Bolsa:
    recurso = obter_bolsa(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_bolsa(db: Session, resource_id: int) -> None:
    recurso = obter_bolsa(db, resource_id)
    db.delete(recurso)
    db.commit()

