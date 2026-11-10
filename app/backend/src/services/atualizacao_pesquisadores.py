from collections.abc import Callable
from uuid import UUID

import httpx
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.enums import PesquisadorStatus
from src.core.exceptions import ExternalLookupError
from src.models import FotoPesquisador, Pesquisador
from src.schemas.atualizacao_pesquisadores import AtualizacaoPesquisadoresResultado
from src.services.ingest_lookup import consultar_perfil_completo_por_lattes
from src.services.privacidade import sanitizar_texto_livre


class RespostaPerfilSimccInvalida(Exception):
    pass


def _consultar_perfil(client: httpx.Client, lattes: str) -> tuple[str | None, str | None]:
    profile = consultar_perfil_completo_por_lattes(
        client, lattes, collection="all"
    )
    if not profile:
        return None, None
    name, _city, _territory, photo_url = profile
    if not name:
        return None, photo_url
    if not isinstance(name, str) or len(name.strip()) > 255 or sanitizar_texto_livre(name) != name:
        raise RespostaPerfilSimccInvalida
    return name.strip(), photo_url


def atualizar_pendentes(
    db: Session,
    tamanho_lote: int,
    apos_id: UUID | None = None,
    ao_processar: Callable[[UUID, AtualizacaoPesquisadoresResultado], None] | None = None,
):
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
                nome, foto_url = _consultar_perfil(client, lattes)
            except (httpx.HTTPError, ExternalLookupError, RespostaPerfilSimccInvalida):
                resultado.erro = "Falha ou resposta inválida da API SIMCC; retome a partir do último ID informado."
                return resultado
            resultado.consultados += 1
            if nome:
                changed = db.execute(update(Pesquisador).where(
                    Pesquisador.id == pesquisador_id,
                    Pesquisador.lattes == lattes,
                    Pesquisador.status == PesquisadorStatus.PENDENTE,
                    filtro_nome_vazio,
                ).values(nome=nome, status=PesquisadorStatus.APROVADO)).rowcount
                if changed:
                    resultado.atualizados += 1
                else:
                    resultado.alterados_concorrentemente += 1
            if foto_url:
                foto = db.scalar(
                    select(FotoPesquisador).where(
                        FotoPesquisador.pesquisador_id == pesquisador_id
                    )
                )
                if foto is None:
                    db.add(FotoPesquisador(pesquisador_id=pesquisador_id, url=foto_url))
                    resultado.fotos_atualizadas += 1
                elif foto.url != foto_url:
                    foto.url = foto_url
                    resultado.fotos_atualizadas += 1
            if nome or foto_url:
                db.commit()
            if not nome:
                resultado.sem_resultado += 1
            resultado.ultimo_id = pesquisador_id
            if ao_processar is not None:
                ao_processar(pesquisador_id, resultado)
    resultado.concluido = len(candidatos) < tamanho_lote
    return resultado
