from uuid import UUID

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.core.config import settings
from src.core.enums import PesquisadorStatus
from src.models import FotoPesquisador, Pesquisador, TerritorioIdentidade
from src.services import atualizacao_pesquisadores as service


@pytest.fixture
def ambiente(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TerritorioIdentidade.__table__.create(engine)
    Pesquisador.__table__.create(engine)
    FotoPesquisador.__table__.create(engine)
    monkeypatch.setattr(settings, "simcc_researchers_url", "https://simcc.test/researchers")
    responses = []
    calls = []
    real_client = httpx.Client

    def responder(request):
        calls.append(request)
        return responses.pop(0)

    monkeypatch.setattr(service.httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(responder), **kwargs))

    yield engine, calls, responses
    engine.dispose()


def id_teste(numero):
    return UUID(int=(10 << 124) + numero)


def pesquisador(numero, lattes, nome=None, status=PesquisadorStatus.PENDENTE, cidade=None):
    return Pesquisador(id=id_teste(numero), lattes=lattes, nome=nome, status=status, cidade=cidade)


def test_atualiza_apenas_pendentes_e_retomada(ambiente):
    engine, calls, responses = ambiente
    with Session(engine) as db:
        db.add_all([pesquisador(1, "111", cidade="Salvador"), pesquisador(2, "222"),
                    pesquisador(3, "333", "Já preenchido"),
                    pesquisador(4, "444", status=PesquisadorStatus.REJEITADO),
                    pesquisador(5, None)])
        db.commit()
    responses.extend([httpx.Response(200, json={"data": [{"lattesId": "111", "nome": "Nome Exemplo", "city": "Outra Cidade", "photoUrl": "https://simcc.test/foto/111.jpg"}]}),
                      httpx.Response(200, json={"data": []})])
    with Session(engine) as db:
        result = service.atualizar_pendentes(db, tamanho_lote=1)
        assert result.atualizados == 1 and result.concluido is False
        result = service.atualizar_pendentes(db, tamanho_lote=2, apos_id=result.ultimo_id)
        assert result.sem_resultado == 1 and result.concluido is True

    assert calls[0].url.params["lattes_id"] == "111"
    assert calls[0].url.params["collection"] == "all"
    with Session(engine) as db:
        items = list(db.scalars(select(Pesquisador).order_by(Pesquisador.id)))
        assert (items[0].nome, items[0].cidade, items[0].status) == ("Nome Exemplo", "Salvador", PesquisadorStatus.APROVADO)
        assert items[1].nome is None and items[3].status == PesquisadorStatus.REJEITADO
        foto = db.scalar(select(FotoPesquisador).where(FotoPesquisador.pesquisador_id == items[0].id))
        assert foto.url == "https://simcc.test/foto/111.jpg"


def test_falha_preserva_ponto_de_retomada(ambiente):
    engine, calls, responses = ambiente
    with Session(engine) as db:
        db.add_all([pesquisador(1, "111"), pesquisador(2, "222")])
        db.commit()
    responses.extend([httpx.Response(200, json={"data": [{"lattesId": "111", "nome": "Nome"}]}),
                      httpx.Response(503, json={"detail": "temporariamente indisponível"})])
    with Session(engine) as db:
        result = service.atualizar_pendentes(db, tamanho_lote=30)
        assert result.atualizados == 1 and "SIMCC" in result.erro and result.ultimo_id == id_teste(1)
    with Session(engine) as db:
        assert db.get(Pesquisador, id_teste(2)).nome is None
    responses.append(httpx.Response(200, json={"data": [{"lattesId": "222", "nome": "Outro"}]}))
    with Session(engine) as db:
        resumed = service.atualizar_pendentes(db, tamanho_lote=30, apos_id=result.ultimo_id)
        assert resumed.atualizados == 1 and resumed.concluido is True
