import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import AreaConhecimentoTipo, BolsaStatus, PesquisadorStatus
from src.models import Bolsa, Ingestao, Pesquisador
from src.services.cep_lookup import consultar_cidade_por_cep, normalizar_cep
from src.services.ingest_lookup import salvar_pesquisador
from src.services.ingest_reader import normalizar, texto_linha
from src.use_cases.v1.ingest.entities import (
    adicionar_palavras_chave,
    obter_area,
    obter_departamento,
    obter_instituicao,
    obter_projeto,
    obter_territorio_identidade,
    obter_unidade,
)


def find_existing_periods(db: Session, lattes: str | None, researcher_id=None):
    if not lattes and researcher_id is None:
        return []
    result = db.execute(
        select(Bolsa.id, Bolsa.quando_iniciou, Bolsa.quando_terminou)
        .join(Pesquisador, Pesquisador.id == Bolsa.pesquisador_id)
        .where(
            Pesquisador.lattes == lattes
            if lattes
            else Pesquisador.id == researcher_id
        )
        .where(Bolsa.status != BolsaStatus.DESCARTADA)
    )
    return list(result)


def create_or_get_researcher(db: Session, cpf: str, identification, cache, counters):
    if cpf in cache:
        return cache[cpf]
    lattes = identification[0]
    cached_by_lattes = cache.get("lattes:" + lattes) if lattes else None
    territory = obter_territorio_identidade(db, identification[3])
    if cached_by_lattes is not None:
        researcher = cached_by_lattes
        if territory is not None:
            researcher.territorio_identidade_id = territory.id
        created = False
    else:
        researcher, created = salvar_pesquisador(
            db, identification, territory.id if territory else None
        )
    cache[cpf] = researcher
    if lattes:
        cache["lattes:" + lattes] = researcher
    counters["pesquisadores_criados" if created else "pesquisadores_atualizados"] += 1
    if researcher.status == PesquisadorStatus.PENDENTE:
        counters["pesquisadores_pendentes"] += 1
    return researcher


def persist_row(
    db: Session, ingestao: Ingestao, number: int, row, indices, researcher,
    start, exit_date, end, is_conflict: bool, counters,
):
    large_area_name = texto_linha(row, indices, "grande area")
    area_name = texto_linha(row, indices, "area")
    subarea_name = texto_linha(row, indices, "subarea")
    large_area, created = obter_area(
        db, large_area_name, AreaConhecimentoTipo.GRANDE_AREA, None
    )
    counters["areas_criadas"] += int(created)
    if large_area is None and (area_name or subarea_name):
        large_area, created = obter_area(
            db, "Grande área não informada", AreaConhecimentoTipo.GRANDE_AREA, None
        )
        counters["areas_criadas"] += int(created)
    area, created = (
        obter_area(db, area_name, AreaConhecimentoTipo.AREA, large_area)
        if large_area
        else (None, False)
    )
    counters["areas_criadas"] += int(created)
    if area is None and subarea_name and large_area is not None:
        area, created = obter_area(
            db, "Área não informada", AreaConhecimentoTipo.AREA, large_area
        )
        counters["areas_criadas"] += int(created)
    subarea, created = (
        obter_area(db, subarea_name, AreaConhecimentoTipo.SUBAREA, area)
        if area and subarea_name
        else (None, False)
    )
    counters["areas_criadas"] += int(created)
    taxonomy_leaf = subarea or area or large_area

    institution = obter_instituicao(
        db,
        texto_linha(row, indices, "instituicao"),
        texto_linha(row, indices, "cep instituicao"),
        texto_linha(row, indices, "sigla instituicao"),
    )
    department = obter_departamento(
        db,
        texto_linha(row, indices, "departamento"),
        texto_linha(row, indices, "unidade"),
        texto_linha(row, indices, "cep departamento"),
        institution.id,
        large_area.id if large_area else None,
    )
    obter_unidade(db, texto_linha(row, indices, "unidade"),
                  texto_linha(row, indices, "cep unidade"), department)

    project, created = obter_projeto(
        db,
        texto_linha(row, indices, "titulo do projeto"),
        texto_linha(row, indices, "resumo do projeto"),
        taxonomy_leaf.id if taxonomy_leaf else None,
    )
    counters["projetos_criados"] += int(created)
    counters["palavras_chave_criadas"] += adicionar_palavras_chave(
        db, row, indices, project
    )
    scholarship = Bolsa(
        quando_iniciou=start,
        data_saida_pesquisador=exit_date,
        quando_terminou=end,
        cep_referencia=cep_referencia(row, indices),
        modalidade=texto_linha(row, indices, "modalidade"),
        nome_curso=texto_linha(row, indices, "nome curso"),
        projeto_id=project.id,
        instituicao_id=institution.id,
        pesquisador_id=researcher.id,
        ingestao_id=ingestao.id,
        linha_origem=number,
        is_conflict=is_conflict,
        status=BolsaStatus.PENDENTE_REVISAO if is_conflict else BolsaStatus.REGULAR,
    )
    db.add(scholarship)
    db.flush()
    counters["bolsas_criadas"] += 1
    counters["bolsas_conflitantes"] += int(is_conflict)
    return scholarship


def cep_referencia(row, indices) -> str | None:
    for column in ("cep unidade", "cep departamento", "cep instituicao"):
        cep = normalizar_cep(texto_linha(row, indices, column))
        if cep:
            return cep
    return None


def atualizar_cidades_das_ultimas_bolsas(
    db: Session,
    researcher_ids: set,
    cep_client: httpx.Client | None,
    cep_city_cache: dict[str, str | None],
    city_territories: dict[str, str],
) -> None:
    if not researcher_ids:
        return
    latest_rows = db.execute(
        select(Bolsa.pesquisador_id, Bolsa.cep_referencia)
        .where(
            Bolsa.pesquisador_id.in_(researcher_ids),
            Bolsa.status != BolsaStatus.DESCARTADA,
        )
        .order_by(
            Bolsa.pesquisador_id,
            Bolsa.quando_iniciou.desc().nulls_last(),
            Bolsa.id.desc(),
        )
    )
    latest_cep: dict = {}
    for researcher_id, cep in latest_rows:
        latest_cep.setdefault(researcher_id, cep)

    for researcher_id, cep in latest_cep.items():
        if not cep or cep_client is None:
            continue
        if cep not in cep_city_cache:
            cep_city_cache[cep] = consultar_cidade_por_cep(cep_client, cep)
        city = cep_city_cache[cep]
        if not city:
            continue
        researcher = db.get(Pesquisador, researcher_id)
        if researcher is None:
            continue
        researcher.cidade = city
        territory_name = city_territories.get(normalizar(city))
        if territory_name:
            territory = obter_territorio_identidade(db, territory_name)
            if territory is not None:
                researcher.territorio_identidade_id = territory.id
        else:
            researcher.territorio_identidade_id = None
