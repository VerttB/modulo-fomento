import csv
import io
import json
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.exceptions import NotAcceptableError
from src.schemas.bolsa import BolsaFiltros
from src.services.bolsa import iterar_bolsas_exportacao
from src.services.populacao_municipios import (
    carregar_populacao_municipios,
    normalizar_municipio,
)
from src.services.privacidade import sanitizar_texto_livre
from src.use_cases.v1.reports.exportacao_bolsistas import (
    relatorio_bolsistas_por_recortes,
)


XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SUPPORTED_FORMATS = {
    "text/csv": ("csv", "text/csv; charset=utf-8"),
    XLSX_MIME: ("xlsx", XLSX_MIME),
    "application/json": ("json", "application/json; charset=utf-8"),
}
ALL_RECORTES = ("territorio", "cidade", "instituicao")
RECORTE_LABELS = {
    "territorio": "Território de identidade",
    "cidade": "Cidade",
    "instituicao": "Instituição",
}


@dataclass(frozen=True)
class ArquivoExportacao:
    conteudo: Iterable[str | bytes]
    media_type: str
    filename: str


def _formato_accept(accept: str | None) -> tuple[str, str]:
    if not accept or accept.strip() in ("", "*/*"):
        return SUPPORTED_FORMATS["text/csv"]
    candidates = []
    for order, item in enumerate(accept.split(",")):
        media_type, *parameters = item.strip().casefold().split(";")
        quality = 1.0
        for parameter in parameters:
            key, _, value = parameter.strip().partition("=")
            if key == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        if quality <= 0:
            continue
        if media_type in SUPPORTED_FORMATS:
            fmt, response_type = SUPPORTED_FORMATS[media_type]
            candidates.append((quality, 2, -order, fmt, response_type))
        elif media_type == "*/*":
            fmt, response_type = SUPPORTED_FORMATS["text/csv"]
            candidates.append((quality, 0, -order, fmt, response_type))
    if not candidates:
        raise NotAcceptableError("Formato não aceito. Use CSV, Excel ou JSON.")
    _, _, _, fmt, response_type = max(candidates)
    return fmt, response_type


def _safe_value(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, str):
        sanitized = sanitizar_texto_livre(value)
        return f"'{sanitized}" if sanitized.startswith(("=", "+", "-", "@")) else sanitized
    return value


def _csv_rows(headers: list[str], rows: Iterable[list]):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(headers)
    yield "\ufeff" + buffer.getvalue()
    for row in rows:
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow([_safe_value(value) for value in row])
        yield buffer.getvalue()


def _xlsx_rows(headers: list[str], rows: Iterable[list]):
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as stream:
        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet("Bolsistas")
        sheet.append(headers)
        for row in rows:
            sheet.append([_safe_value(value) for value in row])
        workbook.save(stream)
        stream.seek(0)
        while chunk := stream.read(1024 * 1024):
            yield chunk


def _json_array(rows: Iterable[dict]):
    yield "["
    first = True
    for row in rows:
        if not first:
            yield ","
        yield json.dumps(row, ensure_ascii=False, default=str)
        first = False
    yield "]"


def _render_table(headers, rows, fmt):
    if fmt == "csv":
        return _csv_rows(headers, rows)
    return _xlsx_rows(headers, rows)


def _summary_rows(report: dict, recortes: list[str], modalities: list[str]):
    rows = [["Total geral", "", "", "", report["total_bolsistas"]] + [
        report["por_modalidade"].get(modality, 0) for modality in modalities
    ]]
    for recorte in recortes:
        for item in report["recortes"].get(recorte, []):
            territory = item.get("territorio_identidade", "")
            city = item.get("cidade", "")
            institution = (
                f"{item['sigla']} — {item['nome']}"
                if item.get("sigla") and item.get("nome")
                else item.get("sigla") or item.get("nome") or ""
            )
            rows.append([
                RECORTE_LABELS[recorte], territory, city, institution,
                item["total_bolsistas"],
                *[item["por_modalidade"].get(modality, 0) for modality in modalities],
            ])
    return rows


def exportar_resumo_bolsistas(
    db: Session,
    filtros: BolsaFiltros,
    recortes: list[str] | None,
    accept: str | None,
) -> ArquivoExportacao:
    formato, media_type = _formato_accept(accept)
    selected = list(dict.fromkeys(recortes or ALL_RECORTES))
    report = relatorio_bolsistas_por_recortes(db, filtros, selected)
    if formato == "json":
        content = (json.dumps(report, ensure_ascii=False, default=str),)
    else:
        modalities = list(report["por_modalidade"])
        headers = [
            "Recorte", "Território de identidade", "Cidade", "Instituição",
            "Total de bolsistas únicos",
            *[f"Modalidade: {modality}" for modality in modalities],
        ]
        rows = _summary_rows(report, selected, modalities)
        content = _render_table(headers, rows, formato)
    suffix = "todos" if set(selected) == set(ALL_RECORTES) else "-".join(selected)
    return ArquivoExportacao(content, media_type, f"resumo-bolsistas-{suffix}.{formato}")


RECORD_FIELDS = (
    ("registro_id", "Registro ID"),
    ("pesquisador", "Pesquisador"),
    ("lattes", "Lattes"),
    ("cidade", "Cidade"),
    ("populacao_estimada", "População estimada"),
    ("territorio_identidade", "Território de identidade"),
    ("projeto", "Projeto"),
    ("resumo", "Resumo"),
    ("grande_area", "Grande área"),
    ("area", "Área"),
    ("subarea", "Subárea"),
    ("instituicao", "Instituição"),
    ("sigla_instituicao", "Sigla instituição"),
    ("modalidade", "Modalidade"),
    ("nome_curso", "Curso"),
    ("data_inicio", "Data inicial"),
    ("data_saida_pesquisador", "Data saída pesquisador"),
    ("data_fim", "Data final"),
    ("cep_referencia", "CEP de referência"),
    ("status", "Status"),
    ("is_conflict", "Em conflito"),
    ("linha_origem", "Linha de origem"),
    ("ingestao_id", "Ingestão ID"),
)


def _registro_exportacao(scholarship, population_by_city):
    researcher = scholarship.pesquisador
    project = scholarship.projeto
    institution = scholarship.instituicao
    taxonomy = project.area_conhecimento
    large_area = area = subarea = None
    if taxonomy is not None:
        kind = getattr(taxonomy.tipo, "value", taxonomy.tipo)
        if kind == "subarea":
            subarea = taxonomy.termo
            area = taxonomy.pai.termo if taxonomy.pai else None
            large_area = taxonomy.pai.pai.termo if taxonomy.pai and taxonomy.pai.pai else None
        elif kind == "area":
            area = taxonomy.termo
            large_area = taxonomy.pai.termo if taxonomy.pai else None
        else:
            large_area = taxonomy.termo
    city = researcher.cidade
    return {
        "registro_id": scholarship.id,
        "pesquisador": researcher.nome,
        "lattes": researcher.lattes,
        "cidade": city,
        "populacao_estimada": (
            population_by_city.get(normalizar_municipio(city), {}).get("populacao_estimada")
            if city else None
        ),
        "territorio_identidade": (
            researcher.territorio_identidade.nome if researcher.territorio_identidade else None
        ),
        "projeto": project.nome,
        "resumo": project.resumo,
        "grande_area": large_area,
        "area": area,
        "subarea": subarea,
        "instituicao": institution.nome,
        "sigla_instituicao": institution.sigla,
        "modalidade": scholarship.modalidade,
        "nome_curso": scholarship.nome_curso,
        "data_inicio": scholarship.quando_iniciou,
        "data_saida_pesquisador": scholarship.data_saida_pesquisador,
        "data_fim": scholarship.quando_terminou,
        "cep_referencia": scholarship.cep_referencia,
        "status": getattr(scholarship.status, "value", scholarship.status),
        "is_conflict": scholarship.is_conflict,
        "linha_origem": scholarship.linha_origem,
        "ingestao_id": scholarship.ingestao_id,
    }


def exportar_registros_bolsistas(
    db: Session,
    filtros: BolsaFiltros,
    termo: str | None,
    accept: str | None,
) -> ArquivoExportacao:
    formato, media_type = _formato_accept(accept)
    population_by_city = carregar_populacao_municipios(
        str(settings.populacao_municipios_csv_path)
    )

    def records():
        for scholarship in iterar_bolsas_exportacao(
            db, **filtros.model_dump(), termo=termo
        ):
            yield _registro_exportacao(scholarship, population_by_city)

    if formato == "json":
        content = _json_array(records())
    else:
        headers = [label for _, label in RECORD_FIELDS]
        rows = ([record[key] for key, _ in RECORD_FIELDS] for record in records())
        content = _render_table(headers, rows, formato)
    return ArquivoExportacao(content, media_type, f"registros-bolsistas.{formato}")
