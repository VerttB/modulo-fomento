from collections.abc import Callable
from uuid import UUID

import httpx
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import PesquisadorStatus
from src.models import Pesquisador
from src.schemas.atualizacao_pesquisadores import AtualizacaoPesquisadoresResultado
from src.services.privacidade import sanitizar_texto_livre


class RespostaOdaInvalida(Exception):
    pass


def _url_oda() -> str:
    url = settings.oda_pesquisadores_url
    if not url or not url.strip():
        raise RuntimeError("Configure ODA_PESQUISADORES_URL antes de executar a atualização.")
    return url


def _consultar_nome(client: httpx.Client, url: str, lattes: str) -> str | None:
    response = client.get(url, params={"page": 1, "size": 30, "lattesId": lattes})
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as error:
        raise RespostaOdaInvalida from error
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise RespostaOdaInvalida
    data = payload["data"]
    if not data:
        return None
    matches = [item for item in data if isinstance(item, dict) and str(item.get("lattesId")) == lattes]
    if len(matches) != 1:
        raise RespostaOdaInvalida
    name = matches[0].get("nome")
    if name is None or (isinstance(name, str) and not name.strip()):
        return None
    if not isinstance(name, str) or len(name.strip()) > 255 or sanitizar_texto_livre(name) != name:
        raise RespostaOdaInvalida
    return name.strip()


def atualizar_pendentes(
    db: Session,
    tamanho_lote: int,
    apos_id: UUID | None = None,
    ao_processar: Callable[[UUID, AtualizacaoPesquisadoresResultado], None] | None = None,
):
    url = _url_oda()
    filtro_nome_vazio = or_(Pesquisador.nome.is_(None), func.trim(Pesquisador.nome) == "")
    query = select(Pesquisador.id, Pesquisador.lattes).where(
        Pesquisador.status == PesquisadorStatus.PENDENTE,
        Pesquisador.lattes.is_not(None), func.trim(Pesquisador.lattes) != "", filtro_nome_vazio,
    ).order_by(Pesquisador.id).limit(tamanho_lote)
    if apos_id:
        query = query.where(Pesquisador.id > apos_id)
    candidatos = db.execute(query).all()
    db.rollback()  # Não mantém uma transação aberta durante a chamada externa.
    resultado = AtualizacaoPesquisadoresResultado(ultimo_id=apos_id)
    with httpx.Client(timeout=settings.external_api_timeout_seconds) as client:
        for pesquisador_id, lattes in candidatos:
            try:
                nome = _consultar_nome(client, url, lattes)
            except (httpx.HTTPError, RespostaOdaInvalida):
                resultado.erro = "Falha ou resposta inválida da API ODA; retome a partir do último ID informado."
                return resultado
            resultado.consultados += 1
            if nome:
                changed = db.execute(update(Pesquisador).where(
                    Pesquisador.id == pesquisador_id,
                    Pesquisador.lattes == lattes,
                    Pesquisador.status == PesquisadorStatus.PENDENTE,
                    filtro_nome_vazio,
                ).values(nome=nome, status=PesquisadorStatus.APROVADO)).rowcount
                db.commit()
                if changed:
                    resultado.atualizados += 1
                else:
                    resultado.alterados_concorrentemente += 1
            else:
                resultado.sem_resultado += 1
            resultado.ultimo_id = pesquisador_id
            if ao_processar is not None:
                ao_processar(pesquisador_id, resultado)
    resultado.concluido = len(candidatos) < tamanho_lote
    return resultado
