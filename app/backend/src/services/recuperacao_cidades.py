from collections import Counter, defaultdict

import httpx
from sqlalchemy import func, or_, select, tuple_, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import BolsaStatus
from src.models import Bolsa, Pesquisador
from src.services.ingest_reader import normalizar
from src.services.territory_csv import load_city_territories
from src.use_cases.v1.ingest.entities import obter_territorio_identidade
from src.use_cases.v1.reports.bolsas import refresh_bolsas_metrics


def consultar_cep(client: httpx.Client, cep: str):
    response = client.get(settings.via_cep_url.format(cep=cep.replace("-", "")))
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as error:
        raise httpx.DecodingError("Resposta inválida do serviço de CEP.") from error
    if not isinstance(data, dict):
        raise httpx.DecodingError("Resposta inválida do serviço de CEP.")
    if data.get("erro"):
        return None
    city, state = data.get("localidade"), data.get("uf")
    if not isinstance(city, str) or not city.strip() or not isinstance(state, str) or len(state.strip()) != 2:
        raise httpx.DecodingError("Resposta incompleta do serviço de CEP.")
    return city.strip(), state.strip().upper()


def recuperar_cidades(db: Session, alternativas=None):
    territories = load_city_territories(settings.territorios_csv_path)
    if not territories:
        raise ValueError("A referência de territórios está vazia ou indisponível.")
    latest = (select(Bolsa.pesquisador_id, Bolsa.id.label("bolsa_id"), Bolsa.cep_referencia,
                     func.row_number().over(partition_by=Bolsa.pesquisador_id,
                         order_by=(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc())).label("posicao"))
              .where(Bolsa.status != BolsaStatus.DESCARTADA).subquery())
    groups = defaultdict(list)
    alternativas = alternativas or {}
    counts = Counter()
    for researcher_id, bolsa_id, cep in db.execute(select(latest.c.pesquisador_id, latest.c.bolsa_id, latest.c.cep_referencia).where(latest.c.posicao == 1)):
        if cep:
            source = alternativas.get(bolsa_id, [])
            candidatos = tuple(source if source and source[0] == cep else [cep])
            groups[candidatos].append((researcher_id, bolsa_id))
        else:
            counts["pesquisadores_sem_cep"] += 1
    db.rollback()
    counts["grupos_de_ceps"] = len(groups)
    last_id = (select(Bolsa.id).where(Bolsa.pesquisador_id == Pesquisador.id, Bolsa.status != BolsaStatus.DESCARTADA)
               .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc()).limit(1).correlate(Pesquisador).scalar_subquery())
    last_cep = (select(Bolsa.cep_referencia).where(Bolsa.pesquisador_id == Pesquisador.id, Bolsa.status != BolsaStatus.DESCARTADA)
                .order_by(Bolsa.quando_iniciou.desc().nulls_last(), Bolsa.id.desc()).limit(1).correlate(Pesquisador).scalar_subquery())
    failures = 0
    cache = {}
    with httpx.Client(timeout=settings.external_api_timeout_seconds) as client:
        for number, (candidatos, pairs) in enumerate(groups.items(), start=1):
            location = None
            erro = False
            selected = None
            for cep in candidatos:
                if cep not in cache:
                    try:
                        cache[cep] = consultar_cep(client, cep)
                        failures = 0
                    except httpx.HTTPError:
                        counts["ceps_falha"] += 1
                        failures += 1
                        erro = True
                        break
                if cache[cep] is not None:
                    location, selected = cache[cep], cep
                    break
            if failures >= 5:
                counts["interrompido_por_falhas"] = 1
                break
            if erro:
                continue
            if location is None:
                counts["grupos_sem_cep_encontrado"] += 1
                counts["pesquisadores_sem_cep_encontrado"] += len(pairs)
                continue
            cidade, uf = location
            territory_name = territories.get(normalizar(cidade)) if uf == "BA" else None
            territory = obter_territorio_identidade(db, territory_name) if territory_name else None
            territory_id = territory.id if territory else None
            if not territory_id:
                counts["pesquisadores_sem_territorio_no_csv"] += len(pairs)
            for start in range(0, len(pairs), 500):
                batch = pairs[start:start + 500]
                if selected != candidatos[0]:
                    changed_ceps = db.execute(update(Bolsa).where(
                        Bolsa.id.in_([bolsa_id for _, bolsa_id in batch]),
                        Bolsa.cep_referencia == candidatos[0],
                    ).values(cep_referencia=selected))
                    counts["ceps_alternativos_atualizados"] += changed_ceps.rowcount
                matched = db.execute(update(Pesquisador).where(
                    Pesquisador.id.in_([researcher_id for researcher_id, _ in batch]),
                    tuple_(Pesquisador.id, last_id, last_cep).in_([(researcher_id, bolsa_id, selected) for researcher_id, bolsa_id in batch]),
                    or_(Pesquisador.cidade.is_distinct_from(cidade),
                        Pesquisador.territorio_identidade_id.is_distinct_from(territory_id)),
                )
                                     .values(cidade=cidade, territorio_identidade_id=territory_id))
                counts["pesquisadores_atualizados"] += matched.rowcount
                db.commit()
            counts["grupos_resolvidos"] += 1
            if number % 20 == 0:
                print(f"Localização: {number}/{len(groups)} grupos verificados.", flush=True)
    counts["ceps_distintos_consultados"] = len(cache)
    try:
        refresh_bolsas_metrics(db.get_bind())
        counts["metricas_atualizadas"] = 1
    except SQLAlchemyError:
        counts["metricas_atualizadas"] = 0
    return dict(counts)
