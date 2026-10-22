from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import IngestaoLinhaStatus
from src.models import Ingestao, IngestaoLinha


def ensure_line_checkpoints(
    db: Session,
    ingestao: Ingestao,
    row_count: int,
    outcomes: dict[int, tuple[IngestaoLinhaStatus, str | None, int | None]],
) -> dict[int, IngestaoLinha]:
    checkpoints = {
        checkpoint.linha_origem: checkpoint
        for checkpoint in db.scalars(
            select(IngestaoLinha).where(IngestaoLinha.ingestao_id == ingestao.id)
        )
    }
    for number in range(2, row_count + 1):
        if number not in checkpoints:
            checkpoint = IngestaoLinha(ingestao_id=ingestao.id, linha_origem=number)
            db.add(checkpoint)
            checkpoints[number] = checkpoint
    db.flush()
    for number in range(2, row_count + 1):
        checkpoint = checkpoints[number]
        if checkpoint.processada:
            continue
        status, reason, duplicate_line = outcomes.get(
            number, (IngestaoLinhaStatus.IGNORADA, "Linha vazia.", None)
        )
        checkpoint.status = status
        checkpoint.motivo = reason
        checkpoint.linha_duplicada_id = (
            checkpoints[duplicate_line].id if duplicate_line in checkpoints else None
        )
    db.commit()
    return checkpoints
