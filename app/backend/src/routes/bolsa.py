import csv
import io
import tempfile
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.enums import BolsaStatus
from src.schemas import BolsaCreate, BolsaRead, BolsaUpdate, PaginatedResponse, EstatisticasBolsas
from src.schemas.bolsa import BolsaFiltros, filtros_bolsa_query
from src.services.bolsa import (
    listar_bolsa,
    obter_bolsa,
    criar_bolsa,
    atualizar_bolsa,
    excluir_bolsa,
    iterar_bolsas_exportacao,
)
from src.use_cases.v1.reports.bolsas import relatorio_bolsas
from src.services.populacao_municipios import (
    carregar_populacao_municipios,
    normalizar_municipio,
)
from src.services.privacidade import sanitizar_texto_livre
from src.services.territory_csv import load_city_territories
from src.services.ingest_reader import normalizar

router = APIRouter(prefix="/bolsas", tags=["Bolsas"])
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _export_value(value):
    if isinstance(value, UUID):
        return str(value)
    if not isinstance(value, str):
        return value
    sanitized = sanitizar_texto_livre(value)
    return f"'{sanitized}" if sanitized.startswith(("=", "+", "-", "@")) else sanitized


def _spreadsheet_response(headers, rows, filename: str, request: Request):
    accept = request.headers.get("accept", "*/*").casefold()
    if XLSX_MEDIA_TYPE in accept:
        def xlsx_stream():
            with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as stream:
                workbook = Workbook(write_only=True)
                sheet = workbook.create_sheet("Bolsistas")
                sheet.append(headers)
                for row in rows:
                    sheet.append([_export_value(value) for value in row])
                workbook.save(stream)
                stream.seek(0)
                while chunk := stream.read(1024 * 1024):
                    yield chunk

        return StreamingResponse(
            xlsx_stream(),
            media_type=XLSX_MEDIA_TYPE,
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )

    if "text/csv" not in accept and "*/*" not in accept:
        raise HTTPException(status_code=406, detail="Formato não aceito. Use CSV ou XLSX.")

    def csv_stream():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
        writer.writerow(headers)
        yield "\ufeff" + buffer.getvalue()
        for row in rows:
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow([_export_value(value) for value in row])
            yield buffer.getvalue()

    return StreamingResponse(
        csv_stream(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@router.get("/exportar-resumo", response_class=StreamingResponse)
def exportar_resumo(
    request: Request,
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    recorte: list[Literal["territorio", "cidade", "instituicao"]] | None = Query(None),
    db: Session = Depends(get_db),
):
    report = relatorio_bolsas(db, **filtros.model_dump())
    city_territories = load_city_territories(settings.territorios_csv_path)
    selected_dimensions = set(recorte or ["territorio", "cidade", "instituicao"])
    rows = []
    if "territorio" in selected_dimensions:
        for item in report["por_territorio_identidade"]:
            rows.append(["Território", item["territorio_identidade"], "", "", item["total"]])
    if "cidade" in selected_dimensions:
        for item in report["por_cidade"]:
            territory = city_territories.get(normalizar(item["cidade"] or ""), "")
            rows.append(["Cidade", territory, item["cidade"], "", item["total"]])
    if "instituicao" in selected_dimensions:
        for item in report["por_instituicao"]:
            institution_name = (
                f"{item['sigla']} — {item['nome']}"
                if item["sigla"] and item["nome"]
                else item["sigla"] or item["nome"] or ""
            )
            rows.append(["Instituição", "", "", institution_name, item["total"]])

    suffix = "todos" if len(selected_dimensions) == 3 else "-".join(
        dimension for dimension in ("territorio", "cidade", "instituicao")
        if dimension in selected_dimensions
    )
    return _spreadsheet_response(
        ["Recorte", "Território de identidade", "Cidade", "Instituição", "Quantidade de registros de bolsistas"],
        rows,
        f"resumo-{suffix}-bolsistas-fapesb",
        request,
    )


@router.get("/", response_model=PaginatedResponse[BolsaRead])
def listar(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    status: BolsaStatus | None = Query(None, description="Filtrar pelo status da bolsa"),
    incluir_conflitos: bool = Query(False, description="Incluir bolsas em revisão de conflito"),
    termo: str | None = Query(None, max_length=150, description="Busca em pessoas, projetos, instituição e curso"),
    db: Session = Depends(get_db),
):
    items, total = listar_bolsa(
        db,
        page=page,
        size=size,
        **filtros.model_dump(),
        status=status,
        incluir_conflitos=incluir_conflitos,
        termo=termo,
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/exportar", response_class=StreamingResponse)
def exportar(
    request: Request,
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    termo: str | None = Query(None, max_length=150),
    db: Session = Depends(get_db),
):
    population_by_city = carregar_populacao_municipios(
        str(settings.populacao_municipios_csv_path)
    )
    headers = [
        "Registro ID", "Pesquisador", "Lattes", "Cidade", "População estimada",
        "Território de identidade", "Projeto", "Resumo", "Grande área", "Área",
        "Subárea", "Instituição", "Sigla instituição", "Modalidade", "Curso",
        "Data inicial", "Data saída pesquisador", "Data final", "CEP de referência",
        "Status", "Em conflito", "Linha de origem", "Ingestão ID",
    ]

    def spreadsheet_rows():
        for scholarship in iterar_bolsas_exportacao(
            db,
            **filtros.model_dump(),
            termo=termo,
        ):
            researcher = scholarship.pesquisador
            project = scholarship.projeto
            institution = scholarship.instituicao
            taxonomy = project.area_conhecimento
            grande_area_nome = area_nome = subarea_nome = None
            if taxonomy is not None:
                tipo = getattr(taxonomy.tipo, "value", taxonomy.tipo)
                if tipo == "subarea":
                    subarea_nome = taxonomy.termo
                    area_nome = taxonomy.pai.termo if taxonomy.pai else None
                    grande_area_nome = (
                        taxonomy.pai.pai.termo
                        if taxonomy.pai and taxonomy.pai.pai
                        else None
                    )
                elif tipo == "area":
                    area_nome = taxonomy.termo
                    grande_area_nome = taxonomy.pai.termo if taxonomy.pai else None
                else:
                    grande_area_nome = taxonomy.termo

            city = researcher.cidade
            population = (
                population_by_city.get(normalizar_municipio(city), {}).get(
                    "populacao_estimada"
                )
                if city
                else None
            )
            row = [
                scholarship.id,
                researcher.nome,
                researcher.lattes,
                city,
                population,
                researcher.territorio_identidade.nome
                if researcher.territorio_identidade
                else None,
                project.nome,
                project.resumo,
                grande_area_nome,
                area_nome,
                subarea_nome,
                institution.nome,
                institution.sigla,
                scholarship.modalidade,
                scholarship.nome_curso,
                scholarship.quando_iniciou,
                scholarship.data_saida_pesquisador,
                scholarship.quando_terminou,
                scholarship.cep_referencia,
                getattr(scholarship.status, "value", scholarship.status),
                "Sim" if scholarship.is_conflict else "Não",
                scholarship.linha_origem,
                scholarship.ingestao_id,
            ]
            yield row

    return _spreadsheet_response(headers, spreadsheet_rows(), "bolsistas-fapesb", request)
@router.get("/estatisticas", response_model=EstatisticasBolsas)
def estatisticas(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    db: Session = Depends(get_db),
):
    return relatorio_bolsas(db, **filtros.model_dump())


@router.get("/{resource_id}", response_model=BolsaRead)
def obter(resource_id: UUID, db: Session = Depends(get_db)):
    return obter_bolsa(db, resource_id)


@router.post("/", response_model=BolsaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: BolsaCreate, db: Session = Depends(get_db)):
    return criar_bolsa(db, payload)


@router.patch("/{resource_id}", response_model=BolsaRead)
def atualizar(resource_id: UUID, payload: BolsaUpdate, db: Session = Depends(get_db)):
    return atualizar_bolsa(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: UUID, db: Session = Depends(get_db)):
    excluir_bolsa(db, resource_id)
