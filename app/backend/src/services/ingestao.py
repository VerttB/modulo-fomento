from uuid import UUID
from contextlib import contextmanager

from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, selectinload

from src.core.exceptions import IngestaoEmAndamentoError, ResourceNotFoundError
from src.core.enums import IngestaoLinhaStatus
from src.models import (
    Bolsa,
    BolsaConflito,
    Ingestao,
    IngestaoExecucao,
    IngestaoLinha,
    IngestaoLinhaEvento,
    Instituicao,
    Pesquisador,
    Projeto,
)
from src.services.privacidade import sanitizar_texto_livre


def listar_ingestoes(db: Session, page: int = 1, size: int = 20):
    total = db.scalar(select(func.count()).select_from(Ingestao)) or 0
    items = list(
        db.scalars(
            select(Ingestao)
            .order_by(Ingestao.iniciada_em.desc())
            .limit(size)
            .offset((page - 1) * size)
        )
    )
    return items, total


def obter_ingestao(db: Session, ingestao_id: UUID) -> Ingestao:
    item = db.get(Ingestao, ingestao_id)
    if item is None:
        raise ResourceNotFoundError("Ingestão não encontrada.")
    return item


def resumo_ingestao(db: Session, ingestao_id: UUID) -> dict:
    obter_ingestao(db, ingestao_id)
    status_counts = db.execute(
        select(IngestaoLinha.status, func.count(IngestaoLinha.id))
        .where(IngestaoLinha.ingestao_id == ingestao_id)
        .group_by(IngestaoLinha.status)
    ).all()
    total_attempts = db.scalar(
        select(func.count(IngestaoExecucao.id)).where(
            IngestaoExecucao.ingestao_id == ingestao_id
        )
    ) or 0
    return {
        "ingestao_id": ingestao_id,
        "total_linhas": sum(count for _, count in status_counts),
        "por_status": {status.value: count for status, count in status_counts},
        "total_execucoes": total_attempts,
    }


def listar_linhas_ingestao(
    db: Session,
    ingestao_id: UUID,
    page: int = 1,
    size: int = 25,
    status: IngestaoLinhaStatus | None = None,
    termo: str | None = None,
):
    obter_ingestao(db, ingestao_id)
    conditions = [IngestaoLinha.ingestao_id == ingestao_id]
    if status is not None:
        conditions.append(IngestaoLinha.status == status)
    if termo:
        pattern = f"%{termo.strip()}%"
        conditions.append(
            or_(
                IngestaoLinha.lattes_id.ilike(pattern),
                IngestaoLinha.pesquisador.has(Pesquisador.nome.ilike(pattern)),
                IngestaoLinha.bolsa.has(
                    Bolsa.projeto.has(Projeto.nome.ilike(pattern))
                ),
                IngestaoLinha.bolsa.has(
                    Bolsa.instituicao.has(Instituicao.nome.ilike(pattern))
                ),
            )
        )
    statement = (
        select(IngestaoLinha)
        .where(*conditions)
        .options(
            selectinload(IngestaoLinha.pesquisador),
            selectinload(IngestaoLinha.linha_duplicada),
            selectinload(IngestaoLinha.bolsa).selectinload(Bolsa.projeto),
            selectinload(IngestaoLinha.bolsa).selectinload(Bolsa.instituicao),
            selectinload(IngestaoLinha.bolsa)
            .selectinload(Bolsa.conflitos)
            .selectinload(BolsaConflito.bolsa_relacionada)
            .selectinload(Bolsa.projeto),
            selectinload(IngestaoLinha.bolsa)
            .selectinload(Bolsa.relacionada_em_conflitos)
            .selectinload(BolsaConflito.bolsa_em_conflito)
            .selectinload(Bolsa.projeto),
        )
        .order_by(IngestaoLinha.linha_origem.asc())
    )
    total = db.scalar(
        select(func.count(IngestaoLinha.id)).where(*conditions)
    ) or 0
    lines = db.scalars(statement.limit(size).offset((page - 1) * size)).all()
    items = []
    for line in lines:
        scholarship = line.bolsa
        project = scholarship.projeto if scholarship else None
        related_scholarships = {}
        if scholarship:
            for conflict in scholarship.conflitos:
                related = conflict.bolsa_relacionada
                if related:
                    related_scholarships[related.id] = {
                        "id": conflict.id,
                        "status": conflict.status,
                        "motivo": conflict.motivo,
                        "bolsa_id": related.id,
                        "modalidade": related.modalidade,
                        "quando_iniciou": related.quando_iniciou,
                        "quando_terminou": related.quando_terminou,
                        "projeto_nome": sanitizar_texto_livre(related.projeto.nome)
                        if related.projeto and related.projeto.nome
                        else None,
                    }
            for conflict in scholarship.relacionada_em_conflitos:
                related = conflict.bolsa_em_conflito
                if related:
                    related_scholarships[related.id] = {
                        "id": conflict.id,
                        "status": conflict.status,
                        "motivo": conflict.motivo,
                        "bolsa_id": related.id,
                        "modalidade": related.modalidade,
                        "quando_iniciou": related.quando_iniciou,
                        "quando_terminou": related.quando_terminou,
                        "projeto_nome": sanitizar_texto_livre(related.projeto.nome)
                        if related.projeto and related.projeto.nome
                        else None,
                    }
        items.append(
            {
                "id": line.id,
                "linha_origem": line.linha_origem,
                "status": line.status,
                "motivo": line.motivo,
                "linha_duplicada": line.linha_duplicada.linha_origem
                if line.linha_duplicada
                else None,
                "atualizada_em": line.atualizada_em,
                "lattes_id": line.lattes_id,
                "pesquisador_id": line.pesquisador_id,
                "pesquisador_nome": line.pesquisador.nome if line.pesquisador else None,
                "projeto_id": project.id if project else None,
                "projeto_nome": sanitizar_texto_livre(project.nome)
                if project and project.nome
                else None,
                "bolsa_id": scholarship.id if scholarship else None,
                "modalidade": scholarship.modalidade if scholarship else None,
                "quando_iniciou": scholarship.quando_iniciou if scholarship else None,
                "quando_terminou": scholarship.quando_terminou if scholarship else None,
                "instituicao_nome": scholarship.instituicao.nome
                if scholarship and scholarship.instituicao
                else None,
                "bolsa_status": scholarship.status if scholarship else None,
                "is_conflict": scholarship.is_conflict if scholarship else None,
                "bolsas_conflitantes": list(related_scholarships.values()),
            }
        )
    return items, total


def listar_execucoes_ingestao(db: Session, ingestao_id: UUID):
    obter_ingestao(db, ingestao_id)
    return list(
        db.scalars(
            select(IngestaoExecucao)
            .where(IngestaoExecucao.ingestao_id == ingestao_id)
            .order_by(IngestaoExecucao.numero.desc())
        )
    )


def listar_eventos_linha(db: Session, ingestao_id: UUID, linha_id: UUID):
    line = db.get(IngestaoLinha, linha_id)
    if line is None or line.ingestao_id != ingestao_id:
        raise ResourceNotFoundError("Linha não encontrada nesta ingestão.")
    events = db.scalars(
        select(IngestaoLinhaEvento)
        .where(IngestaoLinhaEvento.ingestao_linha_id == linha_id)
        .options(
            selectinload(IngestaoLinhaEvento.projeto),
            selectinload(IngestaoLinhaEvento.pesquisador),
            selectinload(IngestaoLinhaEvento.execucao),
        )
        .order_by(IngestaoLinhaEvento.criado_em.desc())
    ).all()
    return [
        {
            "id": event.id,
            "execucao_id": event.execucao_id,
            "execucao_numero": event.execucao.numero if event.execucao else None,
            "status": event.status,
            "motivo": event.motivo,
            "bolsa_id": event.bolsa_id,
            "pesquisador_id": event.pesquisador_id,
            "projeto_id": event.projeto_id,
            "criado_em": event.criado_em,
            "projeto_nome": sanitizar_texto_livre(event.projeto.nome)
            if event.projeto and event.projeto.nome
            else None,
            "pesquisador_nome": event.pesquisador.nome if event.pesquisador else None,
        }
        for event in events
    ]


@contextmanager
def travar_ingestao(engine, ingestao_id: UUID):
    """Impede dois workers de retomarem/processarem o mesmo lote simultaneamente."""
    lock_key = ingestao_id.int & ((1 << 63) - 1)
    connection = engine.connect()
    acquired = False
    try:
        acquired = bool(
            connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_key)"),
                {"lock_key": lock_key},
            ).scalar_one()
        )
        connection.commit()
        if not acquired:
            raise IngestaoEmAndamentoError(
                "Esta ingestão já está sendo processada por outra execução."
            )
        yield
    finally:
        if acquired:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_key)"),
                {"lock_key": lock_key},
            )
            connection.commit()
        connection.close()
