from datetime import date
import hashlib
from types import SimpleNamespace
from uuid import UUID

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.services import recuperacao_cidades as cidades
from src.services.recuperacao_localizacao import linha_confere
from src.services.recuperacao_localizacao import verificar_arquivo
from src.core.enums import IngestaoStatus
from src.core.exceptions import IngestFormatError
from src.use_cases.v1.ingest.persist_entities import cep_referencia


def test_arquivo_precisa_conferir_com_checksum(tmp_path):
    source = tmp_path / "origem.csv"
    source.write_text("cpf_pesquisador;Cep Unidade\n;40000000\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    ingestao = SimpleNamespace(status=IngestaoStatus.FALHA, arquivo_sha256=digest, nome_arquivo="origem.csv")
    assert len(verificar_arquivo(ingestao, source)[0]) == 2
    source.write_text("cpf_pesquisador;Cep Unidade\n;40000001\n", encoding="utf-8")
    with pytest.raises(IngestFormatError, match="checksum"):
        verificar_arquivo(ingestao, source)


def test_prioridade_cep_e_validacao_da_linha():
    indices = {"cep unidade": 0, "cep departamento": 1, "cep instituicao": 2,
               "titulo do projeto": 3, "data inicial": 4, "instituicao": 5}
    row = ["40123-456", "40234-567", "40345-678", "Projeto", "2024-01-01", "Instituição"]
    assert cep_referencia(row, indices) == "40123-456"
    row[0] = None
    assert cep_referencia(row, indices) == "40234-567"
    row[1] = None
    assert cep_referencia(row, indices) == "40345-678"
    bolsa = SimpleNamespace(quando_iniciou=date(2024, 1, 1))
    assert linha_confere(row, indices, None, bolsa, "Projeto", "Instituição", None)
    assert not linha_confere(row, indices, None, bolsa, "Outro", "Instituição", None)


def test_consulta_cep_valida_uf_e_nao_inventa_resultado(monkeypatch):
    monkeypatch.setattr(cidades.settings, "via_cep_url", "https://cep.test/{cep}")
    responses = [httpx.Response(200, json={"localidade": "Salvador", "uf": "BA"}),
                 httpx.Response(200, json={"erro": True}),
                 httpx.Response(200, json={"localidade": "Salvador"})]
    with httpx.Client(transport=httpx.MockTransport(lambda request: responses.pop(0))) as client:
        assert cidades.consultar_cep(client, "40000-000") == ("Salvador", "BA")
        assert cidades.consultar_cep(client, "40000-001") is None
        with pytest.raises(httpx.DecodingError):
            cidades.consultar_cep(client, "40000-002")


def test_cidade_segue_ultima_bolsa_e_ignora_descartada(monkeypatch):
    engine = create_engine("sqlite://")
    ids = [UUID(int=(10 << 124) + i) for i in range(1, 5)]
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE pesquisadores (id CHAR(32) PRIMARY KEY, cidade TEXT, territorio_identidade_id CHAR(32))"))
        connection.execute(text("CREATE TABLE bolsas (id CHAR(32) PRIMARY KEY, pesquisador_id CHAR(32), cep_referencia TEXT, quando_iniciou DATE, status TEXT)"))
        connection.execute(text("CREATE TABLE territorios_identidade (id CHAR(32) PRIMARY KEY, nome TEXT, nome_normalizado TEXT)"))
        connection.execute(text("INSERT INTO pesquisadores(id, cidade) VALUES (:id, 'Cidade antiga')"), {"id": ids[0].hex})
        for bolsa_id, cep, inicio, status in [(ids[1], "40000-001", "2022-01-01", "REGULAR"),
                                               (ids[2], "40000-002", "2024-01-01", "REGULAR"),
                                               (ids[3], "40000-003", "2025-01-01", "DESCARTADA")]:
            connection.execute(text("INSERT INTO bolsas VALUES (:id,:pesquisador,:cep,:inicio,:status)"),
                               {"id": bolsa_id.hex, "pesquisador": ids[0].hex, "cep": cep, "inicio": inicio, "status": status})
    monkeypatch.setattr(cidades, "load_city_territories", lambda path: {"salvador": "Metropolitano"})
    monkeypatch.setattr(cidades, "consultar_cep", lambda client, cep: ("Salvador", "BA") if cep == "40000-004" else None)
    monkeypatch.setattr(cidades, "refresh_bolsas_metrics", lambda engine: None)
    with Session(engine) as db:
        result = cidades.recuperar_cidades(db, {ids[2]: ["40000-002", "40000-004"]})
        assert result["pesquisadores_atualizados"] == 1
        assert result["ceps_alternativos_atualizados"] == 1
        row = db.execute(text("SELECT cidade, territorio_identidade_id FROM pesquisadores")).one()
        assert row.cidade == "Salvador" and row.territorio_identidade_id is not None
        assert db.execute(text("SELECT cep_referencia FROM bolsas WHERE id = :id"), {"id": ids[2].hex}).scalar_one() == "40000-004"
    engine.dispose()
