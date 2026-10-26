from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.enums import IngestaoLinhaStatus
from src.core.enums import IngestaoStatus
from src.core.exceptions import IngestFormatError, IngestaoEmAndamentoError, ResourceNotFoundError
from src.models import Ingestao, IngestaoExecucao, IngestaoLinha, IngestaoLinhaEvento
from src.services.ingest_files import caminho_seguro
from src.services.ingest_reader import ler_planilha, mapear_colunas
from src.use_cases.v1.ingest.rows import prepare_rows
from src.use_cases.v1.ingest.tracking import ensure_line_checkpoints


def reconstruir_rastreabilidade(db: Session, ingestao_id) -> dict:
    ingestao = db.get(Ingestao, ingestao_id)
    if ingestao is None:
        raise ResourceNotFoundError("Ingestão não encontrada.")
    if ingestao.status == IngestaoStatus.PROCESSANDO:
        raise IngestaoEmAndamentoError(
            "A rastreabilidade só pode ser reconstruída após o processamento da ingestão."
        )
    if not ingestao.arquivo_original_path:
        raise IngestFormatError("O arquivo original desta ingestão não está disponível.")
    original_path = caminho_seguro(ingestao.arquivo_original_path)
    if not original_path.is_file():
        raise IngestFormatError("O arquivo original desta ingestão não foi encontrado.")

    rows, epoch = ler_planilha(ingestao.nome_arquivo, original_path)
    if len(rows) < 2:
        raise IngestFormatError("O arquivo não contém cabeçalho e linhas de dados.")
    indices = mapear_colunas(rows[0])
    _, _, _, outcomes = prepare_rows(rows, indices, epoch)

    existing_lines = set(
        db.scalars(
            select(IngestaoLinha.linha_origem).where(
                IngestaoLinha.ingestao_id == ingestao.id
            )
        )
    )
    checkpoints = ensure_line_checkpoints(db, ingestao, len(rows), outcomes)
    recovered_lines = sorted(set(checkpoints) - existing_lines)
    latest_execution = db.scalar(
        select(IngestaoExecucao)
        .where(IngestaoExecucao.ingestao_id == ingestao.id)
        .order_by(IngestaoExecucao.numero.desc())
        .limit(1)
    )
    if latest_execution:
        for line_number in recovered_lines:
            checkpoint = checkpoints[line_number]
            db.add(
                IngestaoLinhaEvento(
                    ingestao_linha_id=checkpoint.id,
                    execucao_id=latest_execution.id,
                    status=checkpoint.status,
                    motivo=checkpoint.motivo,
                    bolsa_id=checkpoint.bolsa_id,
                    pesquisador_id=checkpoint.pesquisador_id,
                )
            )
    db.commit()
    return {
        "ingestao_id": ingestao.id,
        "linhas_reconstruidas": len(recovered_lines),
        "linhas_duplicadas_reconstruidas": sum(
            checkpoints[number].status == IngestaoLinhaStatus.DUPLICADA
            for number in recovered_lines
        ),
    }
