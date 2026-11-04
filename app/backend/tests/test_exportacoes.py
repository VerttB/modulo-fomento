import csv
import io
import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.database import get_db
from src.main import app
from src.services.exportacao_bolsistas import XLSX_MIME, _safe_value, _sanitizar_json


@pytest.fixture
def client():
    url = os.environ.get("EXPORT_TEST_DATABASE_URL", "sqlite://")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, poolclass=StaticPool)
    with engine.begin() as connection:
        for statement in (
            "CREATE TEMPORARY TABLE areas_conhecimento (id TEXT, pai_id TEXT, tipo TEXT, termo TEXT)",
            "CREATE TEMPORARY TABLE projetos (id TEXT, area_conhecimento_id TEXT)",
            "CREATE TEMPORARY TABLE instituicoes (id TEXT, nome TEXT, sigla TEXT)",
            "CREATE TEMPORARY TABLE territorios_identidade (id TEXT, nome TEXT)",
            "CREATE TEMPORARY TABLE pesquisadores (id TEXT, cidade TEXT, territorio_identidade_id TEXT)",
            "CREATE TEMPORARY TABLE bolsas (pesquisador_id TEXT, projeto_id TEXT, instituicao_id TEXT, modalidade TEXT, quando_iniciou DATE, status TEXT)",
        ):
            connection.exec_driver_sql(statement)
        project, institution, territory, first, second = (f"{number:032x}" for number in range(1, 6))
        connection.execute(text("INSERT INTO projetos VALUES (:id, NULL)"), {"id": project})
        connection.execute(text("INSERT INTO instituicoes VALUES (:id, 'Universidade', NULL)"), {"id": institution})
        connection.execute(text("INSERT INTO territorios_identidade VALUES (:id, 'Territorio')"), {"id": territory})
        connection.execute(text("INSERT INTO pesquisadores VALUES (:id, :city, :territory)"), {"id": first, "city": "=Cidade", "territory": territory})
        connection.execute(text("INSERT INTO pesquisadores VALUES (:id, :city, :territory)"), {"id": second, "city": "Salvador", "territory": territory})
        for researcher, modality in ((first, "IC"), (first, "Mestrado"), (second, "IC")):
            connection.execute(
                text("INSERT INTO bolsas VALUES (:researcher, :project, :institution, :modality, '2020-01-01', 'REGULAR')"),
                {"researcher": researcher, "project": project, "institution": institution, "modality": modality},
            )

    def override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def test_resumo_conta_pessoas_e_aplica_filtros_multiplos(client):
    response = client.get(
        "/api/v1/exportacoes/bolsistas/resumo",
        params=[("cidade", "=Cidade"), ("cidade", "Salvador"), ("modalidade", "IC"),
                ("ano_inicio", "2020"), ("recorte", "cidade"), ("recorte", "instituicao")],
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"].endswith('.json"')
    data = response.json()
    assert data["total_bolsistas"] == 2
    assert data["por_modalidade"] == {"IC": 2}
    assert len(data["recortes"]["instituicao"]) == 1
    assert data["recortes"]["instituicao"][0]["total_bolsistas"] == 2

    all_modalities = client.get(
        "/api/v1/exportacoes/bolsistas/resumo?recorte=territorio",
        headers={"Accept": "application/json"},
    ).json()
    assert all_modalities["total_bolsistas"] == 2
    assert all_modalities["por_modalidade"] == {"IC": 2, "Mestrado": 1}
    assert all_modalities["recortes"]["territorio"][0]["total_bolsistas"] == 2


@pytest.mark.parametrize("mime", ["text/csv", XLSX_MIME])
def test_resumo_planilha_sanitiza_formulas_e_preserva_contagem(client, mime):
    response = client.get(
        "/api/v1/exportacoes/bolsistas/resumo?recorte=cidade",
        headers={"Accept": mime},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(mime)
    if mime == "text/csv":
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
    else:
        workbook = load_workbook(io.BytesIO(response.content), data_only=False)
        rows = list(workbook.active.values)
    row = next(row for row in rows if row[2] and "=Cidade" in row[2])
    assert row[2].startswith("'")
    assert int(row[4]) == 1


def test_formato_incompativel_retorna_406(client):
    response = client.get(
        "/api/v1/exportacoes/bolsistas/resumo", headers={"Accept": "application/pdf"}
    )
    assert response.status_code == 406


def test_sanitizacao_de_textos_em_planilhas_e_json():
    assert _safe_value("  =1+1") == "'  =1+1"
    assert _safe_value("\ttexto") == "'\ttexto"
    assert _sanitizar_json({"texto": "CPF 111.222.333-44"}) == {"texto": "CPF [CPF removido]"}


def test_registros_json_encaminha_filtros_e_sanitiza_conteudo(client, monkeypatch):
    import src.services.exportacao_bolsistas as exportacao

    captured = {}
    bolsa = SimpleNamespace(
        id="registro-1", pesquisador=SimpleNamespace(
            nome="Pessoa CPF 111.222.333-44", lattes="123", cidade="Salvador",
            territorio_identidade=None,
        ),
        projeto=SimpleNamespace(nome="Projeto", resumo=None, area_conhecimento=None),
        instituicao=SimpleNamespace(nome="Universidade", sigla="UNI"),
        modalidade="IC", nome_curso=None, quando_iniciou=None,
        data_saida_pesquisador=None, quando_terminou=None, cep_referencia=None,
        status="REGULAR", is_conflict=False, linha_origem=2, ingestao_id=None,
    )

    def iterator(db, **kwargs):
        captured.update(kwargs)
        yield bolsa

    monkeypatch.setattr(exportacao, "iterar_bolsas_exportacao", iterator)
    monkeypatch.setattr(exportacao, "carregar_populacao_municipios", lambda _: {})
    response = client.get(
        "/api/v1/exportacoes/bolsistas/registros",
        params=[("cidade", "Salvador"), ("cidade", "Ilheus"), ("modalidade", "IC"), ("termo", "Projeto")],
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    assert captured["cidade"] == ["Salvador", "Ilheus"]
    assert captured["modalidade"] == ["IC"]
    assert captured["termo"] == "Projeto"
    assert response.json()[0]["pesquisador"] == "Pessoa CPF [CPF removido]"
