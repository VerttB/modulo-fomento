import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.core.enums import IngestaoLinhaStatus, IngestaoStatus
from src.core.exceptions import ExternalLookupError, IngestFormatError, IngestaoEmAndamentoError, ResourceNotFoundError
from src.models import Bolsa, Ingestao, IngestaoExecucao, IngestaoLinha, IngestaoLinhaEvento
from src.schemas.ingest import IngestResponse
from src.services.ingest_files import (
    nome_arquivo_seguro,
    salvar_conteudo_upload,
    salvar_upload,
)
from src.services.ingestao import travar_ingestao
from src.services.privacidade import sanitizar_texto_livre
from src.use_cases.v1.ingest.identification import identify_researchers as _identify_researchers
from src.use_cases.v1.ingest.pipeline import (
    _refresh_metrics_after_persistence,
    run_ingestion,
)


logger = logging.getLogger(__name__)


def retomar_ingestao(db: Session, ingestao_id: UUID, *, somente_processando: bool = False) -> IngestResponse:
    with travar_ingestao(db.get_bind(), ingestao_id):
        db.expire_all()
        ingestao = db.get(Ingestao, ingestao_id)
        if ingestao is None:
            raise ResourceNotFoundError("Ingestão não encontrada.")
        if somente_processando and ingestao.status != IngestaoStatus.PROCESSANDO:
            raise IngestaoEmAndamentoError("Ingestão não está mais disponível para processamento.")
        if ingestao.status == IngestaoStatus.CONCLUIDA:
            raise IngestFormatError("Esta ingestão já foi concluída.")
        interrupted = db.scalars(
            select(IngestaoExecucao).where(
                IngestaoExecucao.ingestao_id == ingestao.id,
                IngestaoExecucao.status == IngestaoStatus.PROCESSANDO,
            )
        ).all()
        for previous in interrupted:
            previous.status = IngestaoStatus.FALHA
            previous.finalizada_em = datetime.now(timezone.utc)
            previous.erro = "Execução interrompida; retomada a partir dos lotes confirmados."
        previous_attempts = db.scalar(
            select(func.max(IngestaoExecucao.numero)).where(
                IngestaoExecucao.ingestao_id == ingestao.id
            )
        ) or 0
        execution = IngestaoExecucao(
            ingestao_id=ingestao.id,
            numero=previous_attempts + 1,
            status=IngestaoStatus.PROCESSANDO,
        )
        db.add(execution)
        ingestao.status = IngestaoStatus.PROCESSANDO
        ingestao.finalizada_em = None
        db.commit()
        db.refresh(execution)
        started = time.perf_counter()
        logger.info("Ingestão %s: tentativa %s iniciada; lendo arquivo e preparando checkpoints", ingestao.id, execution.numero)
        try:
            response = run_ingestion(db, ingestao, execution)
            logger.info(
                "Processamento do lote %s finalizado em %.1fs",
                ingestao.id,
                time.perf_counter() - started,
            )
            return response
        except Exception as error:
            db.rollback()
            failed = db.get(Ingestao, ingestao_id)
            failed_execution = db.get(IngestaoExecucao, execution.id)
            if failed is not None:
                failed.status = IngestaoStatus.FALHA
                failed.finalizada_em = datetime.now(timezone.utc)
            if failed_execution is not None:
                failed_execution.status = IngestaoStatus.FALHA
                failed_execution.finalizada_em = datetime.now(timezone.utc)
                failure_message = (
                    "Serviço externo de identificação indisponível; retome a ingestão quando estiver disponível."
                    if isinstance(error, ExternalLookupError)
                    else f"Falha durante o processamento ({type(error).__name__})."
                )
                failed_execution.erro = failure_message
                checkpoints = db.scalars(
                    select(IngestaoLinha).where(IngestaoLinha.ingestao_id == ingestao_id)
                ).all()
                for checkpoint in checkpoints:
                    scholarship = db.get(Bolsa, checkpoint.bolsa_id) if checkpoint.bolsa_id else None
                    if checkpoint.processada:
                        checkpoint.status = (
                            IngestaoLinhaStatus.INSERIDA_CONFLITO
                            if scholarship is not None and scholarship.is_conflict
                            else IngestaoLinhaStatus.INSERIDA
                        )
                        checkpoint.motivo = (
                            "Bolsa armazenada para revisão por conflito de período."
                            if checkpoint.status == IngestaoLinhaStatus.INSERIDA_CONFLITO
                            else None
                        )
                    elif checkpoint.status == IngestaoLinhaStatus.PENDENTE:
                        checkpoint.motivo = "Não processada; aguardando retomada da ingestão."
                    elif checkpoint.status == IngestaoLinhaStatus.ERRO and not checkpoint.motivo:
                        checkpoint.motivo = failure_message
                    db.add(
                        IngestaoLinhaEvento(
                            ingestao_linha_id=checkpoint.id,
                            execucao_id=failed_execution.id,
                            status=checkpoint.status,
                            motivo=checkpoint.motivo,
                            bolsa_id=checkpoint.bolsa_id,
                            pesquisador_id=checkpoint.pesquisador_id,
                            projeto_id=scholarship.projeto_id if scholarship else None,
                        )
                    )
                db.commit()
            _refresh_metrics_after_persistence(db, [])
            logger.error("Falha no lote de ingestão %s (%s)", ingestao_id, type(error).__name__)
            raise


def registrar_ingestao(
    db: Session, filename: str, content: bytes | BinaryIO
) -> UUID:
    started = time.perf_counter()
    safe_filename = sanitizar_texto_livre(nome_arquivo_seguro(filename))
    ingestao = Ingestao(
        nome_arquivo=safe_filename[:255],
        tipo=Path(safe_filename).suffix.casefold().lstrip(".")[:10] or "desconhecido",
        quantidade_linhas=0,
        status=IngestaoStatus.PROCESSANDO,
    )
    db.add(ingestao)
    db.commit()
    db.refresh(ingestao)
    try:
        if isinstance(content, bytes):
            stored_path, checksum = salvar_conteudo_upload(ingestao.id, safe_filename, content)
        else:
            stored_path, checksum = salvar_upload(ingestao.id, safe_filename, content)
        ingestao.arquivo_original_path = stored_path
        ingestao.arquivo_sha256 = checksum
        ingestao.enfileirada = True
        db.execute(text("SELECT pg_notify('ingestoes_pendentes', '')"))
        db.commit()
        logger.info(
            "Ingestão v1 iniciada: lote=%s arquivo=%s sha256=%s",
            ingestao.id,
            safe_filename,
            checksum,
        )
        return ingestao.id
    except Exception as error:
        db.rollback()
        failed = db.get(Ingestao, ingestao.id)
        if failed is not None:
            failed.status = IngestaoStatus.FALHA
            failed.finalizada_em = datetime.now(timezone.utc)
            if not db.scalar(
                select(func.count(IngestaoExecucao.id)).where(
                    IngestaoExecucao.ingestao_id == failed.id
                )
            ):
                db.add(
                    IngestaoExecucao(
                        ingestao_id=failed.id,
                        numero=1,
                        status=IngestaoStatus.FALHA,
                        iniciada_em=failed.iniciada_em,
                        finalizada_em=failed.finalizada_em,
                        erro="Falha ao arquivar ou iniciar o processamento do arquivo.",
                    )
                )
            db.commit()
        logger.error(
            "Falha ao registrar ingestão %s em %.1fs (%s)",
            ingestao.id,
            time.perf_counter() - started,
            type(error).__name__,
        )
        raise
