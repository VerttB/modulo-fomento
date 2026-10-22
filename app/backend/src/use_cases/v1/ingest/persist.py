from collections import defaultdict

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.enums import BolsaConflitoStatus, BolsaStatus
from src.models import Bolsa, BolsaConflito, Ingestao, IngestaoLinha, Pesquisador
from src.schemas.ingest import IngestResponse
from src.services.ingest_reader import normalizar
from src.use_cases.v1.ingest.persist_entities import (
    atualizar_cidades_das_ultimas_bolsas,
    create_or_get_researcher,
    find_existing_periods,
    persist_row,
)
from src.use_cases.v1.ingest.rows import PreparedRow, periods_overlap


COUNTER_NAMES = (
    "projetos_criados",
    "bolsas_criadas",
    "pesquisadores_criados",
    "pesquisadores_atualizados",
    "pesquisadores_pendentes",
    "palavras_chave_criadas",
    "areas_criadas",
    "bolsas_conflitantes",
)


def persist_rows(
    db: Session,
    ingestao: Ingestao,
    prepared: list[PreparedRow],
    indices: dict[str, int],
    identifications: dict[
        str, tuple[str | None, str | None, str | None, str | None]
    ],
    conflicts_by_line: dict[int, list[int]],
    duplicate_count: int,
    ignored_count: int,
    lookup_errors: list[str] | None = None,
    checkpoints: dict[int, IngestaoLinha] | None = None,
    researcher_cache: dict | None = None,
    cep_client: httpx.Client | None = None,
    cep_city_cache: dict[str, str | None] | None = None,
    city_territories: dict[str, str] | None = None,
) -> IngestResponse:
    counters = {name: 0 for name in COUNTER_NAMES}
    researcher_cache = researcher_cache if researcher_cache is not None else {}
    cep_city_cache = cep_city_cache if cep_city_cache is not None else {}
    city_territories = city_territories if city_territories is not None else {}
    periods_by_researcher = defaultdict(list)
    planned_conflicts = {line: set(others) for line, others in conflicts_by_line.items()}
    rows_by_identity = defaultdict(list)
    for item in prepared:
        number, _, cpf, start, _, end = item
        lattes = identifications[cpf][0]
        identity = "lattes:" + lattes if lattes else "cpf:" + cpf
        if start is not None:
            rows_by_identity[identity].append(item)
    for person_rows in rows_by_identity.values():
        person_rows.sort(key=lambda item: (item[3], item[0]))
        for position, current in enumerate(person_rows):
            for previous in person_rows[:position]:
                if periods_overlap(current[3], current[5], previous[3], previous[5]):
                    planned_conflicts.setdefault(current[0], set()).add(previous[0])
                    planned_conflicts.setdefault(previous[0], set()).add(current[0])

    item_order = sorted(prepared, key=lambda item: (item[0] in planned_conflicts, item[0]))
    scholarships_by_line = {}
    conflict_links = []
    conflict_messages = []
    try:
        for number, row, cpf, start, exit_date, end in item_order:
            identification = identifications[cpf]
            lattes = identification[0]
            researcher = create_or_get_researcher(
                db, cpf, identification, researcher_cache, counters
            )
            period_key = "lattes:" + lattes if lattes else cpf
            if period_key not in periods_by_researcher:
                periods_by_researcher[period_key] = find_existing_periods(
                    db, lattes, researcher.id
                )
            existing_conflicts = [
                (old_id, old_start, old_end)
                for old_id, old_start, old_end in periods_by_researcher[period_key]
                if periods_overlap(start, end, old_start, old_end)
            ]
            is_conflict = number in planned_conflicts or bool(existing_conflicts)
            scholarship = persist_row(
                db, ingestao, number, row, indices, researcher,
                start, exit_date, end, is_conflict, counters,
            )
            scholarships_by_line[number] = scholarship
            for old_id, _, _ in existing_conflicts:
                previous = db.get(Bolsa, old_id)
                if previous is not None and previous.status == BolsaStatus.REGULAR:
                    previous.is_conflict = True
                    previous.status = BolsaStatus.PENDENTE_REVISAO
                conflict_links.append(
                    (scholarship.id, old_id, "Sobreposição com bolsa já cadastrada.")
                )
            if existing_conflicts:
                conflict_messages.append(
                    f"Linha {number}: bolsa armazenada como pendente por sobreposição "
                    "com bolsa(s) já cadastrada(s)."
                )
            if start is not None and not is_conflict:
                periods_by_researcher[period_key].append((scholarship.id, start, end))

        for line, related_lines in planned_conflicts.items():
            for related_line in related_lines:
                if line < related_line:
                    conflict_links.append(
                        (
                            scholarships_by_line[line].id,
                            scholarships_by_line[related_line].id,
                            f"Sobreposição de período entre as linhas {line} e {related_line}.",
                        )
                    )
                    conflict_messages.append(
                        f"Linhas {line} e {related_line}: bolsas armazenadas como "
                        "pendentes por sobreposição de período."
                    )
        for candidate_id, related_id, reason in conflict_links:
            db.add(
                BolsaConflito(
                    bolsa_em_conflito_id=candidate_id,
                    bolsa_relacionada_id=related_id,
                    status=BolsaConflitoStatus.PENDENTE,
                    motivo=reason,
                )
            )
        atualizar_cidades_das_ultimas_bolsas(
            db,
            {scholarship.pesquisador_id for scholarship in scholarships_by_line.values()},
            cep_client,
            cep_city_cache,
            city_territories,
        )
        for number, scholarship in scholarships_by_line.items():
            checkpoint = (checkpoints or {}).get(number)
            if checkpoint is not None:
                checkpoint.processada = True
                checkpoint.bolsa_id = scholarship.id
                checkpoint.pesquisador_id = scholarship.pesquisador_id
                checkpoint.erro = None
        db.flush()
        ingestao.linhas_processadas = db.scalar(
            select(func.count(IngestaoLinha.id)).where(
                IngestaoLinha.ingestao_id == ingestao.id,
                IngestaoLinha.processada.is_(True),
            )
        ) or 0
        ingestao.bolsas_conflitantes = db.scalar(
            select(func.count(Bolsa.id)).where(
                Bolsa.ingestao_id == ingestao.id,
                Bolsa.is_conflict.is_(True),
            )
        ) or 0
        db.commit()
    except Exception:
        db.rollback()
        raise

    return IngestResponse(
        linhas_processadas=counters["bolsas_criadas"],
        linhas_duplicadas=duplicate_count,
        linhas_ignoradas=ignored_count,
        erros=[*(lookup_errors or []), *conflict_messages],
        ingestao_id=ingestao.id,
        **counters,
    )
