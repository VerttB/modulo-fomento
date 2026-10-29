from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from src.core.enums import AreaConhecimentoTipo, BolsaStatus
from src.models import (
    AreaConhecimento,
    Bolsa,
    Instituicao,
    Pesquisador,
    Projeto,
    TerritorioIdentidade,
)
from src.schemas.bolsa import BolsaFiltros


def _valores(value: list[str] | None) -> list[str]:
    return [item.strip() for item in value or [] if item and item.strip()]


def _qualquer(coluna, valores: list[str]):
    return or_(*(coluna.ilike(valor) for valor in valores))


def _consulta_filtrada(filtros: BolsaFiltros):
    selected = aliased(AreaConhecimento)
    parent = aliased(AreaConhecimento)
    root = aliased(AreaConhecimento)
    query = (
        select(
            Bolsa.pesquisador_id.label("pesquisador_id"),
            Bolsa.modalidade.label("modalidade"),
            Pesquisador.cidade.label("cidade"),
            TerritorioIdentidade.nome.label("territorio_identidade"),
            Instituicao.id.label("instituicao_id"),
            Instituicao.sigla.label("instituicao_sigla"),
            Instituicao.nome.label("instituicao_nome"),
        )
        .join(Projeto, Bolsa.projeto_id == Projeto.id)
        .join(Instituicao, Bolsa.instituicao_id == Instituicao.id)
        .join(Pesquisador, Bolsa.pesquisador_id == Pesquisador.id)
        .outerjoin(
            TerritorioIdentidade,
            Pesquisador.territorio_identidade_id == TerritorioIdentidade.id,
        )
        .outerjoin(selected, Projeto.area_conhecimento_id == selected.id)
        .outerjoin(parent, selected.pai_id == parent.id)
        .outerjoin(root, parent.pai_id == root.id)
        .where(
            Bolsa.status.in_(
                [
                    BolsaStatus.REGULAR,
                    BolsaStatus.RESOLVIDA,
                    BolsaStatus.PENDENTE_REVISAO,
                ]
            )
        )
    )
    if filtros.ano_inicio is not None:
        query = query.where(
            func.extract("year", Bolsa.quando_iniciou) >= filtros.ano_inicio
        )
    if filtros.ano_fim is not None:
        query = query.where(
            func.extract("year", Bolsa.quando_iniciou) <= filtros.ano_fim
        )

    for values, column in (
        (_valores(filtros.modalidade), Bolsa.modalidade),
        (_valores(filtros.cidade), Pesquisador.cidade),
        (_valores(filtros.territorio_identidade), TerritorioIdentidade.nome),
    ):
        if values:
            query = query.where(_qualquer(column, values))

    institutions = _valores(filtros.instituicao)
    if institutions:
        query = query.where(
            or_(
                *(
                    Instituicao.nome.ilike(value) | Instituicao.sigla.ilike(value)
                    for value in institutions
                )
            )
        )

    area_conditions = []
    for value in _valores(filtros.area):
        area_conditions.append(
            or_(
                (selected.tipo == AreaConhecimentoTipo.AREA)
                & selected.termo.ilike(value),
                (selected.tipo == AreaConhecimentoTipo.SUBAREA)
                & parent.termo.ilike(value),
            )
        )
    if area_conditions:
        query = query.where(or_(*area_conditions))

    large_area_conditions = []
    for value in _valores(filtros.grande_area):
        large_area_conditions.append(
            or_(
                (selected.tipo == AreaConhecimentoTipo.GRANDE_AREA)
                & selected.termo.ilike(value),
                (selected.tipo == AreaConhecimentoTipo.AREA)
                & parent.termo.ilike(value),
                (selected.tipo == AreaConhecimentoTipo.SUBAREA)
                & root.termo.ilike(value),
            )
        )
    if large_area_conditions:
        query = query.where(or_(*large_area_conditions))
    return query.subquery("bolsistas_filtrados")


def _contagens_por_modalidade(db: Session, source, *dimensions):
    researcher_count = func.count(func.distinct(source.c.pesquisador_id))
    return db.execute(
        select(*dimensions, source.c.modalidade, researcher_count)
        .group_by(*dimensions, source.c.modalidade)
        .order_by(researcher_count.desc())
    ).all()


def relatorio_bolsistas_por_recortes(
    db: Session,
    filtros: BolsaFiltros,
    recortes: list[str],
) -> dict:
    """Conta pesquisadores únicos no total, por modalidade e recorte."""
    source = _consulta_filtrada(filtros)
    total = db.scalar(
        select(func.count(func.distinct(source.c.pesquisador_id)))
    ) or 0
    modality_rows = _contagens_por_modalidade(db, source)
    by_modality = {
        name or "Sem modalidade": quantity for name, quantity in modality_rows
    }
    dimensions = {
        "territorio": ((source.c.territorio_identidade,), "territorio_identidade"),
        "cidade": ((source.c.cidade,), "cidade"),
        "instituicao": (
            (source.c.instituicao_id, source.c.instituicao_sigla, source.c.instituicao_nome),
            "instituicao",
        ),
    }
    grouped = {}
    for key in recortes:
        columns, kind = dimensions[key]
        valid_dimension = columns[0].is_not(None)
        total_count = func.count(func.distinct(source.c.pesquisador_id))
        totals = db.execute(
            select(*columns, total_count)
            .where(valid_dimension)
            .group_by(*columns)
            .order_by(total_count.desc())
        ).all()
        items = {}
        for row in totals:
            values = row[:-1]
            quantity = row[-1]
            identity = values[0]
            if kind == "instituicao":
                identifier, acronym, name = values
                item = {
                    "instituicao_id": str(identifier),
                    "sigla": acronym,
                    "nome": name,
                }
            else:
                item = {kind: identity}
            item["total_bolsistas"] = quantity
            item["por_modalidade"] = {}
            items[identity] = item

        modality_counts = db.execute(
            select(*columns, source.c.modalidade, total_count)
            .where(valid_dimension)
            .group_by(*columns, source.c.modalidade)
            .order_by(total_count.desc())
        ).all()
        for row in modality_counts:
            values = row[:-2]
            modality_name, quantity = row[-2:]
            item = items[values[0]]
            label = modality_name or "Sem modalidade"
            item["por_modalidade"][label] = quantity
        grouped[key] = list(items.values())

    return {
        "medida": "pesquisadores_unicos",
        "total_bolsistas": total,
        "por_modalidade": by_modality,
        "recortes": grouped,
    }
