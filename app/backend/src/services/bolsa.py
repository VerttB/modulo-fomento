from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import Session, aliased, selectinload

from src.core.exceptions import ResourceNotFoundError
from src.core.enums import AreaConhecimentoTipo, BolsaStatus
from src.models import (
    AreaConhecimento,
    Bolsa,
    Instituicao,
    Pesquisador,
    Projeto,
    TerritorioIdentidade,
)


DEFAULT_PAGE_SIZE = 30


def _selected_values(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    values = [value] if isinstance(value, str) else value
    return [item.strip() for item in values if item and item.strip()]


def _matches_any(column, values: list[str]):
    return or_(*(column.ilike(value) for value in values))


def _paginar(db: Session, query, page: int, size: int):
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.limit(size).offset((page - 1) * size)))
    return items, total


def _construir_consulta_bolsas(
    area: str | list[str] | None = None,
    grande_area: str | list[str] | None = None,
    universidade: str | list[str] | None = None,
    cidade: str | list[str] | None = None,
    territorio_identidade: str | list[str] | None = None,
    modalidade: str | list[str] | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    status: BolsaStatus | None = None,
    incluir_conflitos: bool = False,
    termo: str | None = None,
):
    query = select(Bolsa).options(
        selectinload(Bolsa.pesquisador).selectinload(Pesquisador.territorio_identidade),
        selectinload(Bolsa.instituicao),
        selectinload(Bolsa.projeto)
        .selectinload(Projeto.area_conhecimento)
        .selectinload(AreaConhecimento.pai)
        .selectinload(AreaConhecimento.pai),
    )
    if status is None:
        allowed_statuses = [BolsaStatus.REGULAR, BolsaStatus.RESOLVIDA]
        if incluir_conflitos:
            allowed_statuses.append(BolsaStatus.PENDENTE_REVISAO)
        query = query.where(Bolsa.status.in_(allowed_statuses))
    else:
        query = query.where(Bolsa.status == status)
    
    if any([area, grande_area]):
        selected = aliased(AreaConhecimento)
        parent = aliased(AreaConhecimento)
        root = aliased(AreaConhecimento)
        query = (
            query.join(Projeto, Bolsa.projeto_id == Projeto.id)
            .outerjoin(selected, Projeto.area_conhecimento_id == selected.id)
            .outerjoin(parent, selected.pai_id == parent.id)
            .outerjoin(root, parent.pai_id == root.id)
        )
        area_conditions = [
            or_(
                and_(
                    selected.tipo == AreaConhecimentoTipo.AREA,
                    selected.termo.ilike(value),
                ),
                and_(
                    selected.tipo == AreaConhecimentoTipo.SUBAREA,
                    parent.termo.ilike(value),
                )
            )
            for value in _selected_values(area)
        ]
        if area_conditions:
            query = query.where(or_(*area_conditions))
        large_area_conditions = [
            or_(
                and_(
                    selected.tipo == AreaConhecimentoTipo.GRANDE_AREA,
                    selected.termo.ilike(value),
                ),
                and_(
                    selected.tipo == AreaConhecimentoTipo.AREA,
                    parent.termo.ilike(value),
                ),
                and_(
                    selected.tipo == AreaConhecimentoTipo.SUBAREA,
                    root.termo.ilike(value),
                )
            )
            for value in _selected_values(grande_area)
        ]
        if large_area_conditions:
            query = query.where(or_(*large_area_conditions))
    
    university_values = _selected_values(universidade)
    if university_values:
        query = query.join(Instituicao, Bolsa.instituicao_id == Instituicao.id)
        query = query.where(
            or_(
                *(
                    or_(Instituicao.nome.ilike(value), Instituicao.sigla.ilike(value))
                    for value in university_values
                )
            )
        )
    
    if cidade or territorio_identidade:
        query = query.join(Pesquisador, Bolsa.pesquisador_id == Pesquisador.id)
    city_values = _selected_values(cidade)
    if city_values:
        query = query.where(_matches_any(Pesquisador.cidade, city_values))

    territory_values = _selected_values(territorio_identidade)
    if territory_values:
        query = query.join(
            TerritorioIdentidade,
            Pesquisador.territorio_identidade_id == TerritorioIdentidade.id,
        ).where(_matches_any(TerritorioIdentidade.nome, territory_values))
    
    modality_values = _selected_values(modalidade)
    if modality_values:
        query = query.where(_matches_any(Bolsa.modalidade, modality_values))
    
    if ano_inicio:
        query = query.where(
            func.extract('year', Bolsa.quando_iniciou) >= ano_inicio
        )
    
    if ano_fim:
        query = query.where(
            func.extract('year', Bolsa.quando_iniciou) <= ano_fim
        )

    if termo and termo.strip():
        pattern = f"%{termo.strip()}%"
        researcher_search = aliased(Pesquisador)
        project_search = aliased(Projeto)
        institution_search = aliased(Instituicao)
        area_search = aliased(AreaConhecimento)
        query = (
            query.join(
                researcher_search,
                Bolsa.pesquisador_id == researcher_search.id,
            )
            .join(project_search, Bolsa.projeto_id == project_search.id)
            .join(institution_search, Bolsa.instituicao_id == institution_search.id)
            .outerjoin(
                area_search,
                project_search.area_conhecimento_id == area_search.id,
            )
            .where(
                or_(
                    Bolsa.modalidade.ilike(pattern),
                    Bolsa.nome_curso.ilike(pattern),
                    researcher_search.nome.ilike(pattern),
                    researcher_search.lattes.ilike(pattern),
                    researcher_search.cidade.ilike(pattern),
                    project_search.nome.ilike(pattern),
                    project_search.resumo.ilike(pattern),
                    institution_search.nome.ilike(pattern),
                    institution_search.sigla.ilike(pattern),
                    area_search.termo.ilike(pattern),
                )
            )
        )

    return query.order_by(Bolsa.id)


def listar_bolsa(
    db: Session,
    page: int = 1,
    size: int = DEFAULT_PAGE_SIZE,
    area: str | list[str] | None = None,
    grande_area: str | list[str] | None = None,
    universidade: str | list[str] | None = None,
    cidade: str | list[str] | None = None,
    territorio_identidade: str | list[str] | None = None,
    modalidade: str | list[str] | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    status: BolsaStatus | None = None,
    incluir_conflitos: bool = False,
    termo: str | None = None,
) -> tuple[list[Bolsa], int]:
    query = _construir_consulta_bolsas(
        area=area,
        grande_area=grande_area,
        universidade=universidade,
        cidade=cidade,
        territorio_identidade=territorio_identidade,
        modalidade=modalidade,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        status=status,
        incluir_conflitos=incluir_conflitos,
        termo=termo,
    )
    return _paginar(db, query, page, size)


def iterar_bolsas_exportacao(
    db: Session,
    *,
    area: str | list[str] | None = None,
    grande_area: str | list[str] | None = None,
    universidade: str | list[str] | None = None,
    cidade: str | list[str] | None = None,
    territorio_identidade: str | list[str] | None = None,
    modalidade: str | list[str] | None = None,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    termo: str | None = None,
):
    query = _construir_consulta_bolsas(
        area=area,
        grande_area=grande_area,
        universidade=universidade,
        cidade=cidade,
        territorio_identidade=territorio_identidade,
        modalidade=modalidade,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        incluir_conflitos=True,
        termo=termo,
    )
    yield from db.scalars(query.execution_options(yield_per=500))


def obter_bolsa(db: Session, resource_id: UUID) -> Bolsa:
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


def atualizar_bolsa(db: Session, resource_id: UUID, payload: BaseModel) -> Bolsa:
    recurso = obter_bolsa(db, resource_id)
    dados: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(recurso, campo, valor)
    db.commit()
    db.refresh(recurso)
    return recurso


def excluir_bolsa(db: Session, resource_id: UUID) -> None:
    recurso = obter_bolsa(db, resource_id)
    db.delete(recurso)
    db.commit()

