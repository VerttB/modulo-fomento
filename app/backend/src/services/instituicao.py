from typing import Any
from math import ceil
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from src.core.exceptions import ResourceNotFoundError
from src.core.enums import BolsaStatus
from src.models import Bolsa, Instituicao, Pesquisador, Projeto
from src.use_cases.v1.reports.bolsas import relatorio_bolsas


DEFAULT_PAGE_SIZE = 30


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def listar_instituicao(
    db: Session,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    termo: str | None = None,
) -> tuple[list[Instituicao], int]:
    query = select(Instituicao).order_by(Instituicao.id)
    if termo and termo.strip():
        pattern = f"%{termo.strip()}%"
        query = query.where(
            or_(Instituicao.nome.ilike(pattern), Instituicao.sigla.ilike(pattern))
        )
    return _paginar(db, query, page, size)


def obter_perfil_instituicao(db: Session, resource_id: UUID) -> dict:
    instituicao = obter_instituicao(db, resource_id)
    status_considerados = [
        BolsaStatus.REGULAR,
        BolsaStatus.RESOLVIDA,
        BolsaStatus.PENDENTE_REVISAO,
    ]
    bolsa_conditions = (
        Bolsa.instituicao_id == resource_id,
        Bolsa.status.in_(status_considerados),
    )
    total_pesquisadores = db.scalar(
        select(func.count(func.distinct(Bolsa.pesquisador_id))).where(
            *bolsa_conditions
        )
    ) or 0
    total_projetos = db.scalar(
        select(func.count(func.distinct(Bolsa.projeto_id))).where(*bolsa_conditions)
    ) or 0
    return {
        "instituicao": instituicao,
        "total_pesquisadores": total_pesquisadores,
        "total_projetos": total_projetos,
        "estatisticas": relatorio_bolsas(db, instituicao_id=resource_id),
    }


def listar_pesquisadores_da_instituicao(
    db: Session, resource_id: UUID, page: int, size: int
) -> tuple[list[Pesquisador], int]:
    obter_instituicao(db, resource_id)
    statuses = [BolsaStatus.REGULAR, BolsaStatus.RESOLVIDA, BolsaStatus.PENDENTE_REVISAO]
    total = db.scalar(
        select(func.count(func.distinct(Bolsa.pesquisador_id))).where(
            Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses)
        )
    ) or 0
    ultima_bolsa_cep = (
        select(Bolsa.cep_referencia)
        .where(
            Bolsa.pesquisador_id == Pesquisador.id,
            Bolsa.instituicao_id == resource_id,
            Bolsa.status.in_(statuses),
        )
        .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc())
        .limit(1)
        .correlate(Pesquisador)
        .scalar_subquery()
    )
    rows = db.execute(
        select(Pesquisador, ultima_bolsa_cep.label("cep_referencia"))
        .join(Bolsa, Bolsa.pesquisador_id == Pesquisador.id)
        .where(Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses))
        .options(selectinload(Pesquisador.territorio_identidade))
        .distinct()
        .order_by(Pesquisador.nome, Pesquisador.id)
        .limit(size)
        .offset((page - 1) * size)
    ).all()
    items = []
    for researcher, cep in rows:
        researcher.cep_referencia = cep
        items.append(researcher)
    return items, total


def listar_projetos_da_instituicao(
    db: Session, resource_id: UUID, page: int, size: int
) -> tuple[list[Projeto], int]:
    obter_instituicao(db, resource_id)
    statuses = [BolsaStatus.REGULAR, BolsaStatus.RESOLVIDA, BolsaStatus.PENDENTE_REVISAO]
    total = db.scalar(
        select(func.count(func.distinct(Bolsa.projeto_id))).where(
            Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses)
        )
    ) or 0
    query = (
        select(Projeto)
        .join(Bolsa, Bolsa.projeto_id == Projeto.id)
        .where(Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses))
        .options(selectinload(Projeto.area_conhecimento))
        .distinct()
        .order_by(Projeto.nome, Projeto.id)
        .limit(size)
        .offset((page - 1) * size)
    )
    return list(db.scalars(query)), total


def listar_bolsas_da_instituicao(
    db: Session, resource_id: UUID, page: int, size: int
) -> tuple[list[dict], int]:
    obter_instituicao(db, resource_id)
    statuses = [BolsaStatus.REGULAR, BolsaStatus.RESOLVIDA, BolsaStatus.PENDENTE_REVISAO]
    base = select(Bolsa).where(
        Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses)
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(
        select(
            Bolsa.id,
            Bolsa.quando_iniciou,
            Bolsa.quando_terminou,
            Bolsa.modalidade,
            Bolsa.nome_curso,
            Bolsa.status,
            Bolsa.is_conflict,
            Pesquisador.nome.label("pesquisador_nome"),
            Pesquisador.cidade.label("pesquisador_cidade"),
            Projeto.nome.label("projeto_nome"),
        )
        .join(Pesquisador, Pesquisador.id == Bolsa.pesquisador_id)
        .join(Projeto, Projeto.id == Bolsa.projeto_id)
        .where(Bolsa.instituicao_id == resource_id, Bolsa.status.in_(statuses))
        .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id)
        .limit(size)
        .offset((page - 1) * size)
    ).mappings().all()
    return [dict(row) for row in rows], total


def obter_instituicao(db: Session, resource_id: UUID) -> Instituicao:
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


def atualizar_instituicao(db: Session, resource_id: UUID, payload: BaseModel) -> Instituicao:
    recurso = obter_instituicao(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_instituicao(db: Session, resource_id: UUID) -> None:
    recurso = obter_instituicao(db, resource_id)
    db.delete(recurso)
    db.commit()

