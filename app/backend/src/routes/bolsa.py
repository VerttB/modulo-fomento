import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.enums import BolsaStatus
from src.schemas import BolsaCreate, BolsaRead, BolsaUpdate, PaginatedResponse, EstatisticasBolsas
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


@router.get("/exportar-resumo", response_class=StreamingResponse)
def exportar_resumo(
    area: list[str] | None = Query(None),
    grande_area: list[str] | None = Query(None),
    universidade: list[str] | None = Query(None),
    cidade: list[str] | None = Query(None),
    territorio_identidade: list[str] | None = Query(None),
    modalidade: list[str] | None = Query(None),
    ano_inicio: int | None = Query(None, ge=1900, le=2100),
    ano_fim: int | None = Query(None, ge=1900, le=2100),
    db: Session = Depends(get_db),
):
    report = relatorio_bolsas(
        db,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        modalidade=modalidade,
        cidade=cidade,
        instituicao=universidade,
        area=area,
        grande_area=grande_area,
        territorio_identidade=territorio_identidade,
    )
    city_territories = load_city_territories(settings.territorios_csv_path)
    rows = []
    for item in report["por_territorio_identidade"]:
        rows.append(["Território", item["territorio_identidade"], "", "", item["total"]])
    for item in report["por_cidade"]:
        territory = city_territories.get(normalizar(item["cidade"] or ""), "")
        rows.append(["Cidade", territory, item["cidade"], "", item["total"]])
    for item in report["por_instituicao"]:
        university = (
            f"{item['sigla']} — {item['nome']}"
            if item["sigla"] and item["nome"]
            else item["sigla"] or item["nome"] or ""
        )
        rows.append(["Universidade", "", "", university, item["total"]])

    def csv_stream():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
        writer.writerow(
            ["Recorte", "Território de identidade", "Cidade", "Universidade", "Quantidade de registros de bolsistas"]
        )
        yield "\ufeff" + buffer.getvalue()
        for row in rows:
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(
                [
                    f"'{sanitizar_texto_livre(value)}"
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                    else sanitizar_texto_livre(value)
                    if isinstance(value, str)
                    else value
                    for value in row
                ]
            )
            yield buffer.getvalue()

    return StreamingResponse(
        csv_stream(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="resumo-bolsistas-fapesb.csv"'},
    )


@router.get("/", response_model=PaginatedResponse[BolsaRead])
def listar(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    area: list[str] | None = Query(None, description="Filtrar por uma ou mais áreas"),
    grande_area: list[str] | None = Query(None, description="Filtrar por uma ou mais grandes áreas"),
    universidade: list[str] | None = Query(None, description="Filtrar por uma ou mais instituições"),
    cidade: list[str] | None = Query(None, description="Filtrar por um ou mais municípios do pesquisador"),
    territorio_identidade: list[str] | None = Query(None, description="Filtrar por um ou mais territórios de identidade"),
    modalidade: list[str] | None = Query(None, description="Filtrar por uma ou mais modalidades"),
    ano_inicio: int | None = Query(None, ge=1900, le=2100, description="Ano de início (mínimo)"),
    ano_fim: int | None = Query(None, ge=1900, le=2100, description="Ano de fim (máximo)"),
    status: BolsaStatus | None = Query(None, description="Filtrar pelo status da bolsa"),
    incluir_conflitos: bool = Query(False, description="Incluir bolsas em revisão de conflito"),
    termo: str | None = Query(None, max_length=150, description="Busca em pessoas, projetos, instituição e curso"),
    db: Session = Depends(get_db),
):
    items, total = listar_bolsa(
        db, page=page, size=size,
        area=area, grande_area=grande_area,
        universidade=universidade, cidade=cidade,
        territorio_identidade=territorio_identidade,
        modalidade=modalidade, ano_inicio=ano_inicio, ano_fim=ano_fim,
        status=status,
        incluir_conflitos=incluir_conflitos,
        termo=termo,
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/exportar", response_class=StreamingResponse)
def exportar(
    area: list[str] | None = Query(None),
    grande_area: list[str] | None = Query(None),
    universidade: list[str] | None = Query(None),
    cidade: list[str] | None = Query(None),
    territorio_identidade: list[str] | None = Query(None),
    modalidade: list[str] | None = Query(None),
    ano_inicio: int | None = Query(None, ge=1900, le=2100),
    ano_fim: int | None = Query(None, ge=1900, le=2100),
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

    def csv_stream():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
        writer.writerow(headers)
        yield "\ufeff" + buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for scholarship in iterar_bolsas_exportacao(
            db,
            area=area,
            grande_area=grande_area,
            universidade=universidade,
            cidade=cidade,
            territorio_identidade=territorio_identidade,
            modalidade=modalidade,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
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
            writer.writerow(
                [
                    f"'{sanitizar_texto_livre(value)}"
                    if isinstance(value, str)
                    and value.startswith(("=", "+", "-", "@"))
                    else sanitizar_texto_livre(value)
                    if isinstance(value, str)
                    else value
                    for value in row
                ]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        csv_stream(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bolsistas-fapesb.csv"'},
    )
@router.get("/estatisticas", response_model=EstatisticasBolsas)
def estatisticas(
    ano_inicio: int | None = Query(None, ge=1900, le=2100),
    ano_fim: int | None = Query(None, ge=1900, le=2100),
    modalidade: list[str] | None = Query(None),
    cidade: list[str] | None = Query(None),
    instituicao: list[str] | None = Query(None),
    area: list[str] | None = Query(None),
    grande_area: list[str] | None = Query(None),
    territorio_identidade: list[str] | None = Query(None),
    db: Session = Depends(get_db),
):
    return relatorio_bolsas(
        db,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        modalidade=modalidade,
        cidade=cidade,
        instituicao=instituicao,
        area=area,
        grande_area=grande_area,
        territorio_identidade=territorio_identidade,
    )


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
