import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.config import settings
from src.models import Pesquisador, TerritorioIdentidade
from src.services.ingest_reader import normalizar
from src.services.populacao_municipios import carregar_populacao_municipios
from src.services.territory_csv import load_city_territories
from src.use_cases.v1.reports.bolsas import refresh_bolsas_metrics

logger = logging.getLogger(__name__)


def listar_cidades_bahia() -> list[dict]:
    territorios = load_city_territories(settings.territorios_csv_path)
    populacoes = carregar_populacao_municipios(
        str(settings.populacao_municipios_csv_path)
    )
    return [
        {
            "cidade": item["municipio"],
            "territorio_identidade": territorios.get(normalizar(item["municipio"])),
            "populacao_estimada": item["populacao_estimada"],
        }
        for nome_normalizado, item in sorted(
            populacoes.items(), key=lambda entry: entry[1]["municipio"].casefold()
        )
    ]


def sincronizar_territorios_pesquisadores(db: Session) -> dict[str, int | bool]:
    cidade_para_territorio = load_city_territories(settings.territorios_csv_path)
    territorios_por_nome = {
        territorio.nome_normalizado: territorio
        for territorio in db.scalars(select(TerritorioIdentidade)).all()
    }
    pesquisadores = db.scalars(
        select(Pesquisador).where(Pesquisador.cidade.is_not(None))
    ).all()

    atualizados = 0
    sem_correspondencia = 0
    territorios_removidos = 0
    for pesquisador in pesquisadores:
        nome_territorio = cidade_para_territorio.get(normalizar(pesquisador.cidade or ""))
        if not nome_territorio:
            sem_correspondencia += 1
            if pesquisador.territorio_identidade_id is not None:
                pesquisador.territorio_identidade_id = None
                territorios_removidos += 1
            continue

        nome_normalizado = normalizar(nome_territorio)
        territorio = territorios_por_nome.get(nome_normalizado)
        if territorio is None:
            territorio = TerritorioIdentidade(
                nome=nome_territorio,
                nome_normalizado=nome_normalizado,
            )
            db.add(territorio)
            db.flush()
            territorios_por_nome[nome_normalizado] = territorio

        if pesquisador.territorio_identidade_id != territorio.id:
            pesquisador.territorio_identidade_id = territorio.id
            atualizados += 1

    db.commit()
    metricas_atualizadas = True
    try:
        refresh_bolsas_metrics(db.get_bind())
    except SQLAlchemyError:
        metricas_atualizadas = False
        logger.exception(
            "Territórios dos pesquisadores foram atualizados, mas as métricas não foram recalculadas"
        )
    return {
        "pesquisadores_verificados": len(pesquisadores),
        "territorios_atualizados": atualizados,
        "cidades_sem_correspondencia": sem_correspondencia,
        "territorios_removidos": territorios_removidos,
        "metricas_atualizadas": metricas_atualizadas,
    }
