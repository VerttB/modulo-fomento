from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.config import settings
from src.core.database import get_db
from src.core.enums import PesquisadorStatus
from src.main import app
from src.models import Pesquisador, TerritorioIdentidade
from src.services import atualizacao_pesquisadores as service


@pytest.fixture
def ambiente(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TerritorioIdentidade.__table__.create(engine)
    Pesquisador.__table__.create(engine)
    monkeypatch.setattr(settings, "oda_pesquisadores_url", "https://oda.test/pesquisadores")
    monkeypatch.setattr(settings, "oda_atualizacao_token", SecretStr("chave-teste"))
    responses = []
    calls = []
    real_client = httpx.Client

    def responder(request):
        calls.append(request)
        return responses.pop(0)

    monkeypatch.setattr(service.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(responder), **kwargs))

    def db_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = db_override
    with TestClient(app) as client:
        yield client, engine, calls, responses
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def id_teste(numero):
    return UUID(int=(10 << 124) + numero)


def pesquisador(numero, lattes, nome=None, status=PesquisadorStatus.PENDENTE, cidade=None):
    return Pesquisador(id=id_teste(numero), lattes=lattes, nome=nome, status=status, cidade=cidade)


def test_atualiza_apenas_pendentes_e_retomada(ambiente):
    client, engine, calls, responses = ambiente
    with Session(engine) as db:
        db.add_all([pesquisador(1, "111", cidade="Salvador"), pesquisador(2, "222"),
                    pesquisador(3, "333", "Já preenchido"),
                    pesquisador(4, "444", status=PesquisadorStatus.REJEITADO),
                    pesquisador(5, None)])
        db.commit()
    responses.extend([httpx.Response(200, json={"data": [{"lattesId": "111", "nome": "Nome Exemplo"}]}),
                      httpx.Response(200, json={"data": []})])
    route = "/api/v1/administracao/pesquisadores/atualizar-oda"
    assert client.post(route, json={}, headers={"X-Atualizacao-Token": "errada"}).status_code == 403
    assert not calls
    result = client.post(route, json={"tamanho_lote": 1}, headers={"X-Atualizacao-Token": "chave-teste"}).json()
    assert result["atualizados"] == 1 and result["concluido"] is False
    assert calls[0].url.params["lattesId"] == "111"
    result = client.post(route, json={"tamanho_lote": 2, "apos_id": result["ultimo_id"]}, headers={"X-Atualizacao-Token": "chave-teste"}).json()
    assert result["sem_resultado"] == 1 and result["concluido"] is True
    with Session(engine) as db:
        items = list(db.scalars(select(Pesquisador).order_by(Pesquisador.id)))
        assert (items[0].nome, items[0].cidade, items[0].status) == ("Nome Exemplo", "Salvador", PesquisadorStatus.APROVADO)
        assert items[1].nome is None and items[3].status == PesquisadorStatus.REJEITADO


def test_falha_preserva_ponto_de_retomada_e_nao_aceita_lattes_errado(ambiente):
    client, engine, calls, responses = ambiente
    with Session(engine) as db:
        db.add_all([pesquisador(1, "111"), pesquisador(2, "222")])
        db.commit()
    responses.extend([httpx.Response(200, json={"data": [{"lattesId": "111", "nome": "Nome"}]}),
                      httpx.Response(200, json={"data": [{"lattesId": "outro", "nome": "Incorreto"}]})])
    route = "/api/v1/administracao/pesquisadores/atualizar-oda"
    result = client.post(route, json={}, headers={"X-Atualizacao-Token": "chave-teste"}).json()
    assert result["atualizados"] == 1 and result["erro"] and result["ultimo_id"] == str(id_teste(1))
    with Session(engine) as db:
        assert db.get(Pesquisador, id_teste(2)).nome is None
    responses.append(httpx.Response(200, json={"data": [{"lattesId": "222", "nome": "Outro"}]}))
    resumed = client.post(route, json={"apos_id": result["ultimo_id"]}, headers={"X-Atualizacao-Token": "chave-teste"}).json()
    assert resumed["atualizados"] == 1 and resumed["concluido"] is True


def test_rota_desligada_sem_configuracao(ambiente, monkeypatch):
    client, _, calls, _ = ambiente
    monkeypatch.setattr(settings, "oda_atualizacao_token", None)
    assert client.post("/api/v1/administracao/pesquisadores/atualizar-oda", json={}).status_code == 503
    assert not calls
