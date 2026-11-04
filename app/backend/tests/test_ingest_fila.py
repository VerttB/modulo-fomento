import os
from uuid import UUID, uuid4

import pytest
import psycopg
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.enums import IngestaoLinhaStatus, IngestaoStatus
from src.core.exceptions import ExternalLookupError
from src.main import app
from src.models import Ingestao, IngestaoExecucao, IngestaoLinha, IngestaoLinhaEvento
from src.models.base import Base
from src.services.ingestao import travar_ingestao
from src.use_cases.v1.ingest import execute
from src.use_cases.v1.ingest.fila import processar_proxima_ingestao


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    url = os.environ.get("INGEST_QUEUE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Configure INGEST_QUEUE_TEST_DATABASE_URL para um PostgreSQL isolado")
    schema = "ingest_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    Base.metadata.create_all(engine, tables=[Ingestao.__table__, IngestaoExecucao.__table__])
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE ingestoes_linhas (
                id uuid PRIMARY KEY, ingestao_id uuid, linha_origem integer, status text,
                motivo text, linha_duplicada_id uuid, identificacao_concluida boolean,
                lattes_id text, processada boolean, bolsa_id uuid, pesquisador_id uuid,
                erro text, atualizada_em timestamp with time zone
            )
        """))
        connection.execute(text("""
            CREATE TABLE ingestoes_linhas_eventos (
                id uuid PRIMARY KEY, ingestao_linha_id uuid, execucao_id uuid, status text,
                motivo text, bolsa_id uuid, pesquisador_id uuid, projeto_id uuid,
                criado_em timestamp with time zone DEFAULT now()
            )
        """))
    monkeypatch.setattr(settings, "ingestoes_path", tmp_path)
    monkeypatch.setattr(execute, "_refresh_metrics_after_persistence", lambda *args: None)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, engine, tmp_path
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()
    with admin.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()


def concluir(db, ingestao, execucao):
    ingestao.status = IngestaoStatus.CONCLUIDA
    execucao.status = IngestaoStatus.CONCLUIDA
    db.commit()


def enviar(client):
    response = client.post("/api/v1/ingest", files={"arquivo": ("entrada.csv", b"cabecalho\nvalor\n", "text/csv")})
    assert response.status_code == 202
    return UUID(response.json()["ingestao_id"])


def test_upload_enfileira_arquivo_e_worker_processa(ambiente, monkeypatch):
    client, engine, path = ambiente
    monkeypatch.setattr(execute, "run_ingestion", concluir)
    ingestao_id = enviar(client)
    assert (path / str(ingestao_id) / "original.csv").read_bytes() == b"cabecalho\nvalor\n"
    with Session(engine) as db:
        assert db.get(Ingestao, ingestao_id).status == IngestaoStatus.PROCESSANDO
        assert db.scalars(select(IngestaoExecucao)).all() == []
    assert client.post("/api/v1/ingestoes/processar-proxima").status_code == 204
    with Session(engine) as db:
        assert db.get(Ingestao, ingestao_id).status == IngestaoStatus.CONCLUIDA
        assert len(db.scalars(select(IngestaoExecucao)).all()) == 1
    assert client.post("/api/v1/ingestoes/processar-proxima").status_code == 204


def test_recupera_interrupcao_e_ignora_execucao_bloqueada(ambiente, monkeypatch):
    client, engine, _ = ambiente
    monkeypatch.setattr(execute, "run_ingestion", concluir)
    ingestao_id = enviar(client)
    with Session(engine) as db:
        db.add(IngestaoExecucao(ingestao_id=ingestao_id, numero=1, status=IngestaoStatus.PROCESSANDO))
        db.commit()
    with travar_ingestao(engine, ingestao_id):
        with Session(engine) as db:
            assert processar_proxima_ingestao(db) is False
    with Session(engine) as db:
        assert processar_proxima_ingestao(db) is True
        attempts = db.scalars(select(IngestaoExecucao).order_by(IngestaoExecucao.numero)).all()
        assert [item.status for item in attempts] == [IngestaoStatus.FALHA, IngestaoStatus.CONCLUIDA]
        assert attempts[0].finalizada_em is not None


def test_falha_e_registrada_e_nao_reprocessada_automaticamente(ambiente, monkeypatch):
    client, engine, _ = ambiente
    def falhar(*args):
        raise ValueError("erro fictício")
    monkeypatch.setattr(execute, "run_ingestion", falhar)
    ingestao_id = enviar(client)
    assert client.post("/api/v1/ingestoes/processar-proxima").status_code == 204
    with Session(engine) as db:
        assert db.get(Ingestao, ingestao_id).status == IngestaoStatus.FALHA
        assert db.scalar(select(IngestaoExecucao)).status == IngestaoStatus.FALHA
        assert processar_proxima_ingestao(db) is False


def test_ingestao_antiga_nao_e_enfileirada_automaticamente(ambiente, monkeypatch):
    client, engine, _ = ambiente
    monkeypatch.setattr(execute, "run_ingestion", concluir)
    with Session(engine) as db:
        legacy = Ingestao(nome_arquivo="antigo.csv", tipo="csv", quantidade_linhas=0,
                          status=IngestaoStatus.PROCESSANDO, arquivo_original_path="antigo.csv")
        db.add(legacy)
        db.commit()
        assert processar_proxima_ingestao(db) is False
        assert db.get(Ingestao, legacy.id).status == IngestaoStatus.PROCESSANDO


def test_falha_externa_preserva_pendentes_erros_e_duplicatas(ambiente, monkeypatch):
    client, engine, _ = ambiente
    ingestao_id = enviar(client)
    with engine.begin() as connection:
        for number, status, reason in (
            (2, "PENDENTE", None), (3, "ERRO", "Falha na consulta externa do pesquisador."),
            (4, "DUPLICADA", "Duplicata da linha 2."),
        ):
            connection.execute(text("""
                INSERT INTO ingestoes_linhas
                (id, ingestao_id, linha_origem, status, motivo, identificacao_concluida, processada)
                VALUES (:id, :ingestao, :linha, :status, :motivo, false, false)
            """), {"id": uuid4(), "ingestao": ingestao_id, "linha": number, "status": status, "motivo": reason})
    def falhar(*args):
        raise ExternalLookupError("serviço indisponível")
    monkeypatch.setattr(execute, "run_ingestion", falhar)
    client.post("/api/v1/ingestoes/processar-proxima")
    with Session(engine) as db:
        lines = db.scalars(select(IngestaoLinha).order_by(IngestaoLinha.linha_origem)).all()
        assert [line.status for line in lines] == [
            IngestaoLinhaStatus.PENDENTE, IngestaoLinhaStatus.ERRO, IngestaoLinhaStatus.DUPLICADA,
        ]
        assert "aguardando retomada" in lines[0].motivo
        assert lines[1].motivo == "Falha na consulta externa do pesquisador."
        assert len(db.scalars(select(IngestaoLinhaEvento)).all()) == 3


def test_upload_notifica_apos_registrar_a_ingestao(ambiente):
    client, engine, _ = ambiente
    url = engine.url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(url, autocommit=True) as listener:
        listener.execute("LISTEN ingestoes_pendentes")
        ingestao_id = enviar(client)
        notification = next(listener.notifies(timeout=5), None)
        assert notification is not None
        assert notification.payload == ""
        with Session(engine) as db:
            assert db.get(Ingestao, ingestao_id).enfileirada is True


def test_falha_ao_salvar_arquivo_nao_emite_evento(ambiente, monkeypatch):
    client, engine, _ = ambiente
    url = engine.url.set(drivername="postgresql").render_as_string(hide_password=False)
    def falhar(*args):
        raise OSError("erro fictício de armazenamento")
    monkeypatch.setattr(execute, "salvar_upload", falhar)
    with psycopg.connect(url, autocommit=True) as listener:
        listener.execute("LISTEN ingestoes_pendentes")
        with pytest.raises(OSError):
            enviar(client)
        assert next(listener.notifies(timeout=1), None) is None
