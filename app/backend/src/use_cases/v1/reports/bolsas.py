from sqlalchemy import Integer, String, Uuid, column, func, select, table, text
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.config import settings
from src.services.populacao_municipios import (
    carregar_populacao_municipios,
    normalizar_municipio,
)


METRICAS_BOLSAS = table(
    "mv_bolsas_metricas",
    column("ano_inicio", Integer),
    column("modalidade", String),
    column("instituicao_id", Uuid),
    column("instituicao_nome", String),
    column("instituicao_sigla", String),
    column("cidade", String),
    column("territorio_identidade_id", Uuid),
    column("territorio_identidade", String),
    column("grande_area", String),
    column("area", String),
    column("subarea", String),
    column("quantidade", Integer),
)


def _filtered(
    ano_inicio,
    ano_fim,
    modalidade,
    cidade,
    instituicao,
    area,
    grande_area,
    territorio_identidade,
    instituicao_id,
):
    query = select(*METRICAS_BOLSAS.c)
    filters = []
    if ano_inicio is not None:
        filters.append(METRICAS_BOLSAS.c.ano_inicio >= ano_inicio)
    if ano_fim is not None:
        filters.append(METRICAS_BOLSAS.c.ano_inicio <= ano_fim)
    if modalidade:
        filters.append(METRICAS_BOLSAS.c.modalidade == modalidade)
    if cidade:
        filters.append(METRICAS_BOLSAS.c.cidade.ilike(f"%{cidade}%"))
    if instituicao:
        filters.append(
            METRICAS_BOLSAS.c.instituicao_nome.ilike(f"%{instituicao}%")
            | METRICAS_BOLSAS.c.instituicao_sigla.ilike(f"%{instituicao}%")
        )
    if instituicao_id:
        filters.append(METRICAS_BOLSAS.c.instituicao_id == instituicao_id)
    if area:
        filters.append(METRICAS_BOLSAS.c.area.ilike(f"%{area}%"))
    if grande_area:
        filters.append(METRICAS_BOLSAS.c.grande_area.ilike(f"%{grande_area}%"))
    if territorio_identidade:
        filters.append(
            METRICAS_BOLSAS.c.territorio_identidade.ilike(
                f"%{territorio_identidade}%"
            )
        )
    return query.where(*filters).subquery("bolsas_filtradas")


def _aggregate(session: Session, source, *dimensions):
    amount = func.sum(source.c.quantidade)
    return session.execute(
        select(*dimensions, amount)
        .select_from(source)
        .where(*(dimension.is_not(None) for dimension in dimensions))
        .group_by(*dimensions)
        .order_by(amount.desc())
    ).all()


def relatorio_bolsas(
    db: Session,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    modalidade: str | None = None,
    cidade: str | None = None,
    instituicao: str | None = None,
    area: str | None = None,
    grande_area: str | None = None,
    territorio_identidade: str | None = None,
    instituicao_id: UUID | None = None,
) -> dict:
    source = _filtered(
        ano_inicio,
        ano_fim,
        modalidade,
        cidade,
        instituicao,
        area,
        grande_area,
        territorio_identidade,
        instituicao_id,
    )
    total = db.scalar(select(func.sum(source.c.quantidade))) or 0
    modalities = _aggregate(db, source, source.c.modalidade)
    years = _aggregate(db, source, source.c.ano_inicio)
    institutions = _aggregate(
        db,
        source,
        source.c.instituicao_id,
        source.c.instituicao_nome,
        source.c.instituicao_sigla,
    )
    cities = _aggregate(db, source, source.c.cidade)
    population_by_city = carregar_populacao_municipios(
        str(settings.populacao_municipios_csv_path)
    )
    from src.services.territory_csv import load_city_territories

    territory_by_city = load_city_territories(settings.territorios_csv_path)
    population_by_territory: dict[str, int] = {}
    for city_key, territory_name in territory_by_city.items():
        population = population_by_city.get(city_key, {}).get("populacao_estimada")
        if isinstance(population, int) and population > 0:
            territory_key = normalizar_municipio(territory_name)
            population_by_territory[territory_key] = (
                population_by_territory.get(territory_key, 0) + population
            )
    territories = _aggregate(db, source, source.c.territorio_identidade)
    large_areas = _aggregate(db, source, source.c.grande_area)
    areas = _aggregate(db, source, source.c.area)
    subareas = _aggregate(db, source, source.c.area, source.c.subarea)
    return {
        "total": total,
        "por_ano": [
            {"ano": year, "total": count}
            for year, count in years
        ],
        "por_modalidade": {name: count for name, count in modalities},
        "por_instituicao": [
            {"id": identifier, "nome": name, "sigla": acronym, "total": count}
            for identifier, name, acronym, count in institutions
        ],
        "por_cidade": [
            {
                "cidade": name,
                "total": count,
                "populacao_estimada": (
                    population_by_city.get(normalizar_municipio(name), {}).get(
                        "populacao_estimada"
                    )
                    if name
                    else None
                ),
                "bolsas_por_100_mil_habitantes": (
                    round(
                        count
                        * 100_000
                        / population_by_city[normalizar_municipio(name)][
                            "populacao_estimada"
                        ],
                        2,
                    )
                    if name
                    and population_by_city.get(normalizar_municipio(name), {}).get(
                        "populacao_estimada"
                    )
                    else None
                ),
                "bolsas_por_10_mil_habitantes": (
                    round(
                        count
                        * 10_000
                        / population_by_city[normalizar_municipio(name)][
                            "populacao_estimada"
                        ],
                        2,
                    )
                    if name
                    and population_by_city.get(normalizar_municipio(name), {}).get(
                        "populacao_estimada"
                    )
                    else None
                ),
            }
            for name, count in cities
        ],
        "por_territorio_identidade": [
            {
                "territorio_identidade": name,
                "total": count,
                "populacao_estimada": population_by_territory.get(
                    normalizar_municipio(name), 0
                ) or None,
                "bolsas_por_100_mil_habitantes": (
                    round(
                        count * 100_000
                        / population_by_territory[normalizar_municipio(name)],
                        2,
                    )
                    if name
                    and population_by_territory.get(normalizar_municipio(name))
                    else None
                ),
                "bolsas_por_10_mil_habitantes": (
                    round(
                        count
                        * 10_000
                        / population_by_territory[normalizar_municipio(name)],
                        2,
                    )
                    if name
                    and population_by_territory.get(normalizar_municipio(name))
                    else None
                ),
            }
            for name, count in territories
        ],
        "por_grande_area": [
            {"grande_area": name, "total": count} for name, count in large_areas
        ],
        "por_area": [{"area": name, "total": count} for name, count in areas],
        "por_subarea": [
            {"area": area_name, "subarea": subarea_name, "total": count}
            for area_name, subarea_name, count in subareas
        ],
    }


def refresh_bolsas_metrics(engine) -> None:
    """Atualiza os agregados sem bloquear consultas durante a atualização."""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_bolsas_metricas"))
