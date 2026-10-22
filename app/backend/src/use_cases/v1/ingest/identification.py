import logging

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import IngestaoLinhaStatus
from src.core.exceptions import ExternalLookupError
from src.models import Ingestao, IngestaoLinha, Pesquisador
from src.services.ingest_lookup import consultar_perfil_por_lattes, consultar_pesquisador
from src.services.ingest_reader import normalizar
from src.use_cases.v1.ingest.rows import PreparedRow


logger = logging.getLogger(__name__)


def identify_researchers(
    cpfs: list[str],
    city_territories: dict[str, str],
    on_progress=None,
) -> tuple[dict, list[str]]:
    identifications = {}
    lookup_failed = False
    with httpx.Client(timeout=settings.external_api_timeout_seconds) as client:
        for position, cpf in enumerate(cpfs, start=1):
            try:
                lattes, name, city, territory = consultar_pesquisador(client, cpf)
                territory = city_territories.get(normalizar(city or ""))
                identifications[cpf] = (lattes, name, city, territory)
            except ExternalLookupError:
                identifications[cpf] = (None, None, None, None)
                lookup_failed = True
            if position % 50 == 0 or position == len(cpfs):
                logger.info("Identificação externa: %d/%d pessoas", position, len(cpfs))
            if on_progress and (
                position % settings.ingest_checkpoint_interval == 0
                or position == len(cpfs)
            ):
                on_progress(position, len(cpfs))
    errors = (
        ["Uma ou mais consultas externas falharam; retome o lote para tentar novamente."]
        if lookup_failed
        else []
    )
    return identifications, errors


def identify_with_checkpoints(
    db: Session,
    ingestao: Ingestao,
    prepared: list[PreparedRow],
    checkpoints: dict[int, IngestaoLinha],
    city_territories: dict[str, str],
) -> tuple[dict[str, tuple[str | None, str | None, str | None, str | None]], list[str]]:
    rows_by_cpf: dict[str, list[PreparedRow]] = {}
    for item in prepared:
        rows_by_cpf.setdefault(item[2], []).append(item)

    identifications = {}
    errors = []
    cpfs = sorted(rows_by_cpf)
    total = len(cpfs)
    complete = 0
    client = httpx.Client(timeout=settings.external_api_timeout_seconds)
    try:
        for position, cpf in enumerate(cpfs, start=1):
            person_rows = rows_by_cpf[cpf]
            person_checkpoints = [checkpoints[item[0]] for item in person_rows]
            saved = next(
                (item for item in person_checkpoints if item.identificacao_concluida),
                None,
            )
            if saved is not None:
                try:
                    persisted_researcher_id = next(
                        (
                            checkpoint.pesquisador_id
                            for checkpoint in person_checkpoints
                            if checkpoint.processada and checkpoint.pesquisador_id
                        ),
                        None,
                    )
                    persisted_researcher = (
                        db.get(Pesquisador, persisted_researcher_id)
                        if persisted_researcher_id
                        else None
                    )
                    if persisted_researcher is not None:
                        name = persisted_researcher.nome
                        city = persisted_researcher.cidade
                        territory = city_territories.get(normalizar(city or ""))
                    elif saved.lattes_id:
                        name, city, territory = consultar_perfil_por_lattes(
                            client, saved.lattes_id
                        )
                        territory = city_territories.get(normalizar(city or ""))
                    else:
                        name, city, territory = None, None, None
                    identifications[cpf] = (saved.lattes_id, name, city, territory)
                    complete += 1
                except ExternalLookupError as error:
                    errors.append(str(error))
            else:
                try:
                    lattes, name, city, territory = consultar_pesquisador(client, cpf)
                    territory = city_territories.get(normalizar(city or ""))
                    identifications[cpf] = (lattes, name, city, territory)
                    for checkpoint in person_checkpoints:
                        checkpoint.identificacao_concluida = True
                        checkpoint.lattes_id = lattes
                        checkpoint.erro = None
                    complete += 1
                except ExternalLookupError:
                    message = (
                        f"Falha na consulta externa para as linhas "
                        f"{min(item[0] for item in person_rows)}–"
                        f"{max(item[0] for item in person_rows)}."
                    )
                    errors.append(message)
                    for checkpoint in person_checkpoints:
                        checkpoint.erro = message
                        checkpoint.status = IngestaoLinhaStatus.ERRO
                        checkpoint.motivo = "Falha na consulta externa do pesquisador."

            ingestao.pesquisadores_total = total
            ingestao.pesquisadores_consultados = complete
            if position % settings.ingest_checkpoint_interval == 0 or position == total:
                db.commit()
                logger.info(
                    "Identificação externa do lote %s: %d/%d pesquisadores",
                    ingestao.id,
                    complete,
                    total,
                )
    finally:
        client.close()
    db.commit()
    return identifications, errors
