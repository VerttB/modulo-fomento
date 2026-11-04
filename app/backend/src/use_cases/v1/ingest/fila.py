import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import IngestaoStatus
from src.core.exceptions import IngestaoEmAndamentoError, ResourceNotFoundError
from src.models import Ingestao
from src.use_cases.v1.ingest.execute import retomar_ingestao

logger = logging.getLogger(__name__)


def processar_proxima_ingestao(db: Session) -> bool:
    """Processa uma ingestão pendente ou recupera uma execução interrompida."""
    candidatos = db.scalars(
        select(Ingestao.id)
        .where(
            Ingestao.status == IngestaoStatus.PROCESSANDO,
            Ingestao.enfileirada.is_(True),
            Ingestao.arquivo_original_path.is_not(None),
        )
        .order_by(Ingestao.iniciada_em, Ingestao.id)
    ).all()
    for ingestao_id in candidatos:
        try:
            retomar_ingestao(db, ingestao_id, somente_processando=True)
            return True
        except (IngestaoEmAndamentoError, ResourceNotFoundError):
            db.rollback()
            continue
        except Exception as error:
            db.rollback()
            logger.error("Falha ao processar ingestão %s (%s)", ingestao_id, type(error).__name__)
            return True
    return False
