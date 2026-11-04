from uuid import uuid4

import pytest

from src.services import hop_dispatcher
from src.services.hop_docker import DockerHopError


def test_disparador_drena_fila_e_para_quando_vazia(monkeypatch):
    first, second = uuid4(), uuid4()
    pending = iter([first, second, second, None, None])
    monkeypatch.setattr(hop_dispatcher, "proxima_ingestao", lambda: next(pending))
    class Hop:
        def __init__(self):
            self.calls = []
        def executar(self, item):
            self.calls.append(item)
            return 0
    hop = Hop()
    hop_dispatcher.processar_pendencias(hop)
    assert hop.calls == [first, second]


def test_disparador_retorna_erro_em_falha_do_hop(monkeypatch):
    monkeypatch.setattr(hop_dispatcher, "proxima_ingestao", lambda: uuid4())
    class Hop:
        def executar(self, item):
            return 1
    with pytest.raises(DockerHopError):
        hop_dispatcher.processar_pendencias(Hop())
