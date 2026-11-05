from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services import maria


@pytest.fixture
def maria_api(monkeypatch):
    calls = []
    responses = []
    original_client = httpx.AsyncClient

    def handle(request):
        calls.append(request)
        status, body = responses.pop(0)
        return httpx.Response(status, json=body)

    monkeypatch.setattr(maria.settings, "maria_api_url", "https://maria.test/api-maria")
    monkeypatch.setattr(maria.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handle), **kwargs))
    with TestClient(app) as client:
        yield client, calls, responses


def test_conversas_e_mensagens_encaminham_contrato(maria_api):
    client, calls, responses = maria_api
    conversation_id = str(uuid4())
    base = "/api/v1/maria/conversations"
    responses.extend([(200, {"conversations": [], "total": 0}), (201, {"id": conversation_id}),
                      (200, {"id": conversation_id}), (200, {"messages": []}),
                      (201, {"user_message": {}, "assistant_message": {}})])
    assert client.get(base, params={"offset": 30, "limit": 30}).json()["total"] == 0
    assert calls[-1].url.params["offset"] == "30"
    assert client.post(base, json={"title": None}).status_code == 201
    assert calls[-1].read() == b'{"title":null}'
    assert client.get(f"{base}/{conversation_id}").json()["id"] == conversation_id
    assert client.get(f"{base}/{conversation_id}/messages").json() == {"messages": []}
    assert client.post(f"{base}/{conversation_id}/messages", json={"content": "Olá"}).status_code == 201
    assert calls[-1].url.path.endswith(f"/conversations/{conversation_id}/messages")
    assert calls[-1].read().decode("utf-8") == '{"content":"Olá"}'


def test_validacao_e_falha_externa(maria_api):
    client, calls, responses = maria_api
    base = "/api/v1/maria/conversations"
    conversation_id = str(uuid4())
    assert client.get(base, params={"limit": 101}).status_code == 422
    assert client.post(f"{base}/{conversation_id}/messages", json={"content": ""}).status_code == 422
    assert not calls
    responses.append((404, {"detail": "not found"}))
    assert client.get(f"{base}/{conversation_id}").status_code == 404
    responses.append((503, {"detail": "private details"}))
    result = client.get(base)
    assert result.status_code == 502
    assert "private details" not in result.text
