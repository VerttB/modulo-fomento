import logging
import time

import psycopg
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src.core.config import HopDispatcherConfig, settings
from src.core.database import engine
from src.core.enums import IngestaoStatus
from src.models import Ingestao
from src.services.hop_docker import HopDocker, DockerHopError


logger = logging.getLogger(__name__)
LOCK_ID = 0x484F505155455545


def proxima_ingestao():
    with Session(engine) as db:
        return db.scalar(
            select(Ingestao.id)
            .where(
                Ingestao.status == IngestaoStatus.PROCESSANDO,
                Ingestao.enfileirada.is_(True),
                Ingestao.arquivo_original_path.is_not(None),
            )
            .order_by(Ingestao.iniciada_em, Ingestao.id)
            .limit(1)
        )


def processar_pendencias(hop: HopDocker):
    while ingestao_id := proxima_ingestao():
        logger.info("Iniciando Hop para ingestão %s", ingestao_id)
        exit_code = hop.executar(ingestao_id)
        logger.info("Hop finalizado para ingestão %s com código %d", ingestao_id, exit_code)
        if exit_code or proxima_ingestao() == ingestao_id:
            raise DockerHopError("A execução do Hop falhou; a fila será reavaliada.")


def executar_disparador(config: HopDispatcherConfig):
    connection_url = make_url(settings.database_url).set(drivername="postgresql")
    hop = HopDocker(config)
    while True:
        try:
            with psycopg.connect(connection_url.render_as_string(hide_password=False), autocommit=True) as listener:
                locked = listener.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,)).fetchone()[0]
                if not locked:
                    raise RuntimeError("Outro disparador já está ativo.")
                listener.execute("LISTEN ingestoes_pendentes")
                notifications = listener.notifies()
                logger.info("Disparador Hop conectado; verificando pendências.")
                while True:
                    processar_pendencias(hop)
                    next(notifications)
        except Exception as error:
            detail = str(error) if isinstance(error, DockerHopError) else type(error).__name__
            logger.error("Disparador Hop indisponível (%s); tentando novamente em %d segundos", detail, config.hop_retry_delay_seconds)
            time.sleep(config.hop_retry_delay_seconds)
