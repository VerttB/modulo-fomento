from datetime import date
from typing import Any

from src.core.exceptions import IngestFormatError
from src.core.enums import IngestaoLinhaStatus
from src.services.ingest_reader import normalizar_cpf, parse_data, texto_linha


PreparedRow = tuple[int, list[Any], str, date | None, date | None, date | None]


def distinct_cpfs(prepared: list[PreparedRow]) -> set[str]:
    return {item[2] for item in prepared}


def prepare_rows(
    rows: list[list[Any]], indices: dict[str, int], epoch: Any = None
) -> tuple[list[PreparedRow], int, dict[int, list[int]], dict[int, tuple[IngestaoLinhaStatus, str | None, int | None]]]:
    prepared: list[PreparedRow] = []
    seen: dict[tuple[str, date | None, date | None, date | None], int] = {}
    duplicate_count = 0
    outcomes = {}

    for number, row in enumerate(rows[1:], start=2):
        if not any(value is not None and str(value).strip() for value in row):
            outcomes[number] = (IngestaoLinhaStatus.IGNORADA, "Linha vazia.", None)
            continue
        try:
            cpf_value = texto_linha(row, indices, "cpf_pesquisador")
            if not cpf_value:
                raise IngestFormatError("CPF do pesquisador vazio.")
            cpf = normalizar_cpf(cpf_value)
            start = parse_data(texto_linha(row, indices, "data inicial"), epoch)
            researcher_exit = parse_data(texto_linha(row, indices, "data final 1"), epoch)
            scholarship_end = parse_data(texto_linha(row, indices, "data final 2"), epoch)
            if start and researcher_exit and researcher_exit < start:
                raise IngestFormatError(
                    "A primeira Data Final não pode ser anterior à Data Inicial."
                )
            if start and scholarship_end and scholarship_end < start:
                raise IngestFormatError(
                    "A última Data Final não pode ser anterior à Data Inicial."
                )
            key = (cpf, start, researcher_exit, scholarship_end)
            if key in seen:
                duplicate_count += 1
                outcomes[number] = (
                    IngestaoLinhaStatus.DUPLICADA,
                    f"Duplicata da linha {seen[key]}.",
                    seen[key],
                )
                continue
            seen[key] = number
            prepared.append((number, row, cpf, start, researcher_exit, scholarship_end))
            outcomes[number] = (IngestaoLinhaStatus.PENDENTE, None, None)
        except IngestFormatError as error:
            outcomes[number] = (IngestaoLinhaStatus.INVALIDA, str(error), None)

    rows_by_cpf: dict[str, list[PreparedRow]] = {}
    for item in prepared:
        if item[3] is not None:
            rows_by_cpf.setdefault(item[2], []).append(item)

    conflicts: dict[int, set[int]] = {}
    for person_rows in rows_by_cpf.values():
        person_rows.sort(key=lambda item: item[3])
        for position, current in enumerate(person_rows):
            number, _, _, start, _, end = current
            for previous in person_rows[:position]:
                previous_number, _, _, previous_start, _, previous_end = previous
                if periods_overlap(start, end, previous_start, previous_end):
                    conflicts.setdefault(number, set()).add(previous_number)
                    conflicts.setdefault(previous_number, set()).add(number)

    if not prepared and not any(
        status == IngestaoLinhaStatus.INVALIDA for status, _, _ in outcomes.values()
    ):
        raise IngestFormatError("O arquivo não contém linhas de dados.")
    return (
        prepared,
        duplicate_count,
        {number: sorted(lines) for number, lines in conflicts.items()},
        outcomes,
    )


def periods_overlap(
    start_a: date | None, end_a: date | None, start_b: date | None, end_b: date | None
) -> bool:
    if start_a is None or start_b is None:
        return False
    return (end_a is None or start_b < end_a) and (end_b is None or start_a < end_b)
