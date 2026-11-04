from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.core.exceptions import ExternalLookupError
from src.use_cases.v1.ingest import identification


def dados(count):
    prepared = [(number + 2, None, f"{number:011d}") for number in range(count)]
    checkpoints = {
        item[0]: SimpleNamespace(
            identificacao_concluida=False, processada=False, pesquisador_id=None,
            lattes_id=None, erro=None, status=None, motivo=None,
        ) for item in prepared
    }
    return prepared, checkpoints


def test_interrompe_apos_falhas_consecutivas_e_salva_checkpoints(monkeypatch):
    calls = []
    def falhar(client, cpf):
        calls.append(1)
        raise ExternalLookupError("indisponível")
    monkeypatch.setattr(identification, "consultar_pesquisador", falhar)
    prepared, checkpoints = dados(8)
    db = Mock()
    with pytest.raises(ExternalLookupError, match="falhas consecutivas"):
        identification.identify_with_checkpoints(db, SimpleNamespace(id="lote"), prepared, checkpoints, {})
    assert len(calls) == identification.MAX_FALHAS_EXTERNAS_CONSECUTIVAS
    db.commit.assert_called()
    assert checkpoints[2].erro is not None
    assert checkpoints[7].erro is None


def test_resposta_sem_resultado_reinicia_contagem_de_falhas(monkeypatch):
    attempts = iter([False] * 4 + [True] + [False] * 4)
    def consultar(client, cpf):
        if not next(attempts):
            raise ExternalLookupError("indisponível")
        return None, None, None, None
    monkeypatch.setattr(identification, "consultar_pesquisador", consultar)
    prepared, checkpoints = dados(9)
    result, errors = identification.identify_with_checkpoints(
        Mock(), SimpleNamespace(id="lote"), prepared, checkpoints, {}
    )
    assert len(result) == 1
    assert len(errors) == 8
