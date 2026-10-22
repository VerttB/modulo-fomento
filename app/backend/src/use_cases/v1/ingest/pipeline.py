import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import IngestaoLinhaStatus, IngestaoStatus
from src.core.exceptions import IngestFormatError
from src.models import Bolsa, Ingestao, IngestaoExecucao, IngestaoLinhaEvento, Pesquisador
from src.schemas.ingest import IngestResponse
from src.services.ingest_files import caminho_seguro, salvar_versao_com_lattes
from src.services.ingest_reader import ler_planilha, mapear_colunas
from src.services.territory_csv import load_city_territories
from src.use_cases.v1.ingest.identification import identify_with_checkpoints
from src.use_cases.v1.ingest.persist import COUNTER_NAMES, persist_rows
from src.use_cases.v1.ingest.rows import PreparedRow, distinct_cpfs, prepare_rows
from src.use_cases.v1.ingest.tracking import ensure_line_checkpoints
from src.use_cases.v1.reports.bolsas import refresh_bolsas_metrics


logger = logging.getLogger(__name__)


def _refresh_metrics_after_persistence(db: Session, errors: list[str]) -> None:
    try:
        refresh_bolsas_metrics(db.get_bind())
    except SQLAlchemyError:
        logger.exception("Ingestão persistida, mas a view materializada não foi atualizada")
        errors.append(
            "A importação foi persistida, mas as métricas precisam ser atualizadas "
            "com o comando de refresh da view materializada."
        )


def _build_response(
    ingestao: Ingestao,
    counters: dict[str, int],
    duplicate_count: int,
    errors: list[str],
) -> IngestResponse:
    response_counters = {
        name: value for name, value in counters.items() if name != "bolsas_conflitantes"
    }
    return IngestResponse(
        ingestao_id=ingestao.id,
        linhas_processadas=ingestao.linhas_processadas,
        linhas_duplicadas=duplicate_count,
        linhas_ignoradas=ingestao.linhas_ignoradas,
        erros=errors,
        bolsas_conflitantes=ingestao.bolsas_conflitantes,
        **response_counters,
    )


def run_ingestion(
    db: Session, ingestao: Ingestao, execution: IngestaoExecucao
) -> IngestResponse:
    if not ingestao.arquivo_original_path:
        raise IngestFormatError("O arquivo original deste lote não está disponível.")
    original_path = caminho_seguro(ingestao.arquivo_original_path)
    if not original_path.is_file():
        raise IngestFormatError("O arquivo original deste lote não foi encontrado no armazenamento.")

    rows, epoch = ler_planilha(ingestao.nome_arquivo, original_path)
    if len(rows) < 2:
        raise IngestFormatError("O arquivo precisa conter cabeçalho e ao menos uma linha.")
    indices = mapear_colunas(rows[0])
    prepared, duplicates, conflicts_by_line, outcomes = prepare_rows(rows, indices, epoch)
    cpfs = sorted(distinct_cpfs(prepared))
    ingestao.quantidade_linhas = len(rows) - 1
    ingestao.linhas_duplicadas = duplicates
    ingestao.linhas_ignoradas = sum(
        status in (IngestaoLinhaStatus.IGNORADA, IngestaoLinhaStatus.INVALIDA)
        for status, _, _ in outcomes.values()
    )
    ingestao.pesquisadores_total = len(cpfs)
    checkpoints = ensure_line_checkpoints(db, ingestao, len(rows), outcomes)

    researcher_cache = {}
    rows_by_cpf: dict[str, list[PreparedRow]] = {}
    for item in prepared:
        rows_by_cpf.setdefault(item[2], []).append(item)
    for cpf, person_rows in rows_by_cpf.items():
        existing_researcher_id = next(
            (
                checkpoints[item[0]].pesquisador_id
                for item in person_rows
                if checkpoints[item[0]].pesquisador_id is not None
            ),
            None,
        )
        if existing_researcher_id is not None:
            researcher = db.get(Pesquisador, existing_researcher_id)
            if researcher is not None:
                researcher_cache[cpf] = researcher

    city_territories = load_city_territories(settings.territorios_csv_path)
    identifications, lookup_errors = identify_with_checkpoints(
        db, ingestao, prepared, checkpoints, city_territories
    )
    errors = list(lookup_errors)
    counters = {name: 0 for name in COUNTER_NAMES}
    cep_city_cache: dict[str, str | None] = {}
    ready = [
        item
        for item in prepared
        if item[2] in identifications and not checkpoints[item[0]].processada
    ]

    with httpx.Client(timeout=settings.external_api_timeout_seconds) as cep_client:
        for start in range(0, len(ready), settings.ingest_batch_size):
            chunk = ready[start : start + settings.ingest_batch_size]
            chunk_lines = {item[0] for item in chunk}
            chunk_conflicts = {
                line: [other for other in conflicts_by_line.get(line, []) if other in chunk_lines]
                for line in chunk_lines
                if conflicts_by_line.get(line)
            }
            response = persist_rows(
                db,
                ingestao,
                chunk,
                indices,
                identifications,
                chunk_conflicts,
                0,
                0,
                checkpoints={line: checkpoints[line] for line in chunk_lines},
                researcher_cache=researcher_cache,
                cep_client=cep_client,
                cep_city_cache=cep_city_cache,
                city_territories=city_territories,
            )
            for name in COUNTER_NAMES:
                counters[name] += getattr(response, name)
            errors.extend(response.erros)
            logger.info(
                "Lote %s: persistidas %d de %d linhas elegíveis",
                ingestao.id,
                min(start + len(chunk), len(ready)),
                len(ready),
            )

    unfinished = [
        item[0]
        for item in prepared
        if not checkpoints[item[0]].processada and item[2] in identifications
    ]
    if unfinished:
        raise RuntimeError(f"Linhas sem checkpoint de conclusão: {unfinished[:10]}")

    for checkpoint in checkpoints.values():
        scholarship = db.get(Bolsa, checkpoint.bolsa_id) if checkpoint.bolsa_id else None
        if checkpoint.processada:
            checkpoint.status = (
                IngestaoLinhaStatus.INSERIDA_CONFLITO
                if scholarship is not None and scholarship.is_conflict
                else IngestaoLinhaStatus.INSERIDA
            )
            checkpoint.motivo = (
                "Bolsa armazenada para revisão por conflito de período."
                if checkpoint.status == IngestaoLinhaStatus.INSERIDA_CONFLITO
                else None
            )
        db.add(
            IngestaoLinhaEvento(
                ingestao_linha_id=checkpoint.id,
                execucao_id=execution.id,
                status=checkpoint.status,
                motivo=checkpoint.motivo,
                bolsa_id=checkpoint.bolsa_id,
                pesquisador_id=checkpoint.pesquisador_id,
                projeto_id=scholarship.projeto_id if scholarship else None,
            )
        )
    db.flush()

    if lookup_errors:
        ingestao.status = IngestaoStatus.FALHA
        ingestao.finalizada_em = datetime.now(timezone.utc)
        execution.status = IngestaoStatus.FALHA
        execution.finalizada_em = datetime.now(timezone.utc)
        db.commit()
        _refresh_metrics_after_persistence(db, errors)
        return _build_response(ingestao, counters, duplicates, errors)

    treated_path = salvar_versao_com_lattes(
        ingestao.id, ingestao.nome_arquivo, rows, indices, identifications
    )
    ingestao.arquivo_path = treated_path
    ingestao.status = IngestaoStatus.CONCLUIDA
    ingestao.finalizada_em = datetime.now(timezone.utc)
    execution.status = IngestaoStatus.CONCLUIDA
    execution.finalizada_em = datetime.now(timezone.utc)
    db.commit()

    _refresh_metrics_after_persistence(db, errors)
    db.refresh(ingestao)
    return _build_response(ingestao, counters, duplicates, errors)
