from datetime import date
import io
from pathlib import Path

import pytest

from src.core.exceptions import IngestFormatError
from src.services.ingest_reader import mapear_colunas
from src.models import Bolsa, BolsaConflito, Ingestao, Pesquisador, Projeto
from src.schemas import PesquisadorRead, ProjetoCreate, ProjetoRead
from src.use_cases.v1.ingest.rows import distinct_cpfs, prepare_rows
from src.services.ingest_lookup import _extrair_perfil
from src.services.ingest_files import (
    caminho_seguro,
    salvar_upload,
    salvar_versao_com_lattes,
)
from src.services.cep_lookup import consultar_cidade_por_cep, normalizar_cep
from src.use_cases.v1.ingest.persist import _cep_referencia
from src.core.config import settings
from src.models import IngestaoLinha
from uuid import uuid4
from unittest.mock import Mock
from src.services.territory_csv import load_city_territories
from src.use_cases.v1.ingest import execute as ingest_execute
from src.use_cases.v1.reports.bolsas import _filtered
from src.services.populacao_municipios import (
    carregar_populacao_municipios,
    normalizar_municipio,
)
from src.services.territorio_identidade import listar_cidades_bahia
from src.services.privacidade import sanitizar_texto_livre
from src.services.bolsa import _construir_consulta_bolsas
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError


HEADERS = [
    "CPF Pesquisador",
    "Titulo do Projeto",
    "Data Inicial",
    "Data Final",
    "Data Final",
]


def test_header_maps_cpf_temporarily_and_two_final_dates():
    columns = mapear_colunas(HEADERS)

    assert columns["cpf_pesquisador"] == 0
    assert columns["data final 1"] == 3
    assert columns["data final 2"] == 4


def test_duplicate_rows_are_deduplicated_by_cpf_and_three_dates():
    rows = [
        HEADERS,
        ["52998224725", "Projeto A", "01/01/2024", "01/06/2024", "31/12/2024"],
        ["529.982.247-25", "Outra descrição", "01/01/2024", "01/06/2024", "31/12/2024"],
    ]

    prepared, duplicates, conflicts = prepare_rows(rows, mapear_colunas(HEADERS))

    assert len(prepared) == 1
    assert duplicates == 1
    assert conflicts == {}
    assert prepared[0][3:] == (
        date(2024, 1, 1),
        date(2024, 6, 1),
        date(2024, 12, 31),
    )


def test_overlapping_scholarships_for_same_cpf_are_kept_and_marked_as_conflicts():
    rows = [
        HEADERS,
        ["52998224725", "Projeto A", "01/01/2024", "", "31/12/2024"],
        ["52998224725", "Projeto B", "01/06/2024", "", "31/12/2024"],
    ]

    prepared, _, conflicts = prepare_rows(rows, mapear_colunas(HEADERS))

    assert [item[0] for item in prepared] == [2, 3]
    assert conflicts == {2: [3], 3: [2]}


def test_same_cpf_with_distinct_periods_keeps_rows_and_looks_up_once():
    rows = [
        HEADERS,
        ["52998224725", "Projeto A", "01/01/2024", "", "30/06/2024"],
        ["52998224725", "Projeto B", "01/07/2024", "", "31/12/2024"],
    ]

    prepared, duplicates, conflicts = prepare_rows(rows, mapear_colunas(HEADERS))

    assert len(prepared) == 2
    assert duplicates == 0
    assert conflicts == {}
    assert distinct_cpfs(prepared) == {"52998224725"}


def test_external_lookup_runs_once_for_each_distinct_cpf(monkeypatch):
    calls = []

    def fake_lookup(client, cpf):
        calls.append(cpf)
        return "lattes-123", "Pessoa", "Salvador", None

    monkeypatch.setattr(ingest_execute, "consultar_pesquisador", fake_lookup)
    identifications, errors = ingest_execute._identify_researchers(
        ["52998224725"], {}
    )

    assert calls == ["52998224725"]
    assert identifications["52998224725"][0] == "lattes-123"
    assert errors == []


def test_city_territory_csv_is_normalized(tmp_path):
    path = tmp_path / "territorios.csv"
    path.write_text(
        "Município;Território de Identidade\nFeira de Santana;Portal do Sertão\n",
        encoding="utf-8",
    )

    assert load_city_territories(path)["feira de santana"] == "Portal do Sertão"


def test_simcc_profile_territory_is_optional():
    assert _extrair_perfil(
        {"name": "Pessoa", "city": "Salvador", "territorio_identidade": "Metropolitano"}
    ) == ("Pessoa", "Salvador", "Metropolitano")


def test_missing_cpf_column_is_a_format_error():
    with pytest.raises(IngestFormatError, match="cpf_pesquisador"):
        mapear_colunas(["Titulo do Projeto", "Data Inicial"])


def test_public_researcher_schema_never_exposes_cpf():
    assert "cpf" not in PesquisadorRead.model_fields


def test_project_stores_only_a_reference_to_the_taxonomy_tree():
    assert "area_conhecimento_id" in Projeto.__table__.columns
    assert not {"grande_area", "area", "subarea"}.intersection(
        Projeto.__table__.columns.keys()
    )
    assert "area_conhecimento_id" in ProjetoCreate.model_fields


def test_researcher_links_territory_by_foreign_key():
    assert "territorio_identidade_id" in Pesquisador.__table__.columns
    assert Pesquisador.__table__.c.territorio_identidade_id.foreign_keys


def test_ingested_scholarships_keep_batch_and_source_line():
    assert "nome_arquivo" in Ingestao.__table__.columns
    assert "quantidade_linhas" in Ingestao.__table__.columns
    assert "tipo" in Ingestao.__table__.columns
    assert "arquivo_original_path" in Ingestao.__table__.columns
    assert "arquivo_path" in Ingestao.__table__.columns
    assert Bolsa.__table__.c.ingestao_id.foreign_keys
    assert "linha_origem" in Bolsa.__table__.columns


def test_ingest_line_checkpoint_never_stores_cpf():
    columns = IngestaoLinha.__table__.columns.keys()

    assert "linha_origem" in columns
    assert "lattes_id" in columns
    assert "processada" in columns
    assert not any("cpf" in column.casefold() for column in columns)
    assert not {"pesquisador_nome", "pesquisador_cidade", "territorio_identidade"}.intersection(columns)


def test_scholarship_cep_uses_unit_then_department_then_institution():
    columns = mapear_colunas([
        "CPF Pesquisador", "CEP Unidade", "CEP Departamento", "CEP Instituição"
    ])
    row = ["52998224725", "", "44001-234", "40000-000"]

    assert _cep_referencia(row, columns) == "44001-234"
    assert _cep_referencia(["52998224725", "44002-345", "44001-234", "40000-000"], columns) == "44002-345"
    assert _cep_referencia(["52998224725", "", "", "40000-000"], columns) == "40000-000"
    assert normalizar_cep("44.001-234") == "44001-234"
    assert normalizar_cep("123") is None


def test_cep_city_comes_from_viacep_localidade():
    import httpx

    def respond(request):
        assert request.url.path == "/ws/44001234/json/"
        return httpx.Response(200, json={"localidade": "Feira de Santana"})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert consultar_cidade_por_cep(client, "44001-234") == "Feira de Santana"


def test_original_upload_is_saved_in_ingestion_storage_with_checksum(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ingestoes_path", tmp_path)
    ingestao_id = uuid4()

    relative_path, checksum = salvar_upload(
        ingestao_id,
        "planilha.csv",
        io.BytesIO(b"CPF;Nome\n123;Pessoa\n"),
    )

    original = caminho_seguro(relative_path)
    assert original == tmp_path / str(ingestao_id) / "original.csv"
    assert original.read_bytes() == b"CPF;Nome\n123;Pessoa\n"
    assert len(checksum) == 64


def test_sanitized_copy_replaces_cpf_with_lattes(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ingestoes_path", tmp_path)
    ingestao_id = uuid4()
    rows = [
        ["CPF Pesquisador", "Titulo do Projeto"],
        ["529.982.247-25", "Projeto"],
    ]
    indices = mapear_colunas(rows[0])

    relative_path = salvar_versao_com_lattes(
        ingestao_id,
        "dados.xlsx",
        rows,
        indices,
        {"52998224725": ("1234567890123456", "Pessoa", "Salvador", None)},
    )

    sanitized = caminho_seguro(relative_path).read_text(encoding="utf-8-sig")
    assert "CPF" not in sanitized
    assert "Lattes Pesquisador" in sanitized
    assert "1234567890123456" in sanitized


def test_conflict_link_is_an_association_between_two_scholarships():
    assert BolsaConflito.__table__.c.bolsa_em_conflito_id.foreign_keys
    assert BolsaConflito.__table__.c.bolsa_relacionada_id.foreign_keys
    assert {"status", "motivo"}.issubset(BolsaConflito.__table__.columns.keys())


def test_reports_read_the_materialized_view_and_apply_filters():
    source = _filtered(2024, 2025, "IC", "Salvador", None, None, None, None)
    statement = source.select().compile(dialect=postgresql.dialect())

    assert "mv_bolsas_metricas" in str(statement)
    assert "ano_inicio" in str(statement)
    assert "cidade" in str(statement)


def test_metric_refresh_failure_is_reported_after_persisted_rows(monkeypatch):
    db = Mock()
    db.get_bind.return_value = object()
    errors = []

    def fail_refresh(engine):
        raise SQLAlchemyError("refresh failed")

    monkeypatch.setattr(ingest_execute, "refresh_bolsas_metrics", fail_refresh)

    ingest_execute._refresh_metrics_after_persistence(db, errors)

    assert len(errors) == 1
    assert "refresh" in errors[0]


def test_bahia_population_dataset_has_all_municipalities_and_normalizes_names():
    dataset = Path(__file__).resolve().parents[1] / "IBGE_Cidades_Bahia.csv"
    municipalities = carregar_populacao_municipios(str(dataset))

    assert len(municipalities) == 417
    assert municipalities[normalizar_municipio("Água Fria")]["populacao_estimada"] == 14798


def test_all_bahia_cities_have_population_and_identity_territory():
    cities = listar_cidades_bahia()

    assert len(cities) == 417
    assert all(city["populacao_estimada"] for city in cities)
    assert all(city["territorio_identidade"] for city in cities)


def test_scholarship_search_covers_related_entities():
    statement = _construir_consulta_bolsas(termo="Salvador").compile(
        dialect=postgresql.dialect()
    )
    sql = str(statement).casefold()

    assert "ilike" in sql
    assert "pesquisadores" in sql
    assert "projetos" in sql
    assert "instituicoes" in sql


def test_free_text_fields_mask_cpf_values():
    assert sanitizar_texto_livre("Resumo 529.982.247-25 e 52998224725") == (
        "Resumo [CPF removido] e [CPF removido]"
    )
    assert sanitizar_texto_livre(None) is None


def test_project_response_masks_cpf_in_legacy_summary():
    projeto = ProjetoRead.model_validate({
        "id": uuid4(),
        "nome": "Projeto",
        "resumo": "Texto antigo 529.982.247-25",
        "area_conhecimento_id": None,
        "area_conhecimento": None,
    })

    assert "529.982.247-25" not in projeto.model_dump_json()
    assert "[CPF removido]" in projeto.model_dump_json()
