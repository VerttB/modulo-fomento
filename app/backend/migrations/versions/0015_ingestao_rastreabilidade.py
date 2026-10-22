"""Adiciona resultados e histórico de tentativas da ingestão.

Revision ID: 0015_ingest_trace
Revises: 0014_metrics_pending
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0015_ingest_trace"
down_revision: str | None = "0014_metrics_pending"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LINE_STATUSES = (
    "PENDENTE",
    "INSERIDA",
    "INSERIDA_CONFLITO",
    "DUPLICADA",
    "IGNORADA",
    "INVALIDA",
    "ERRO",
)
INGEST_STATUSES = ("PROCESSANDO", "CONCLUIDA", "FALHA")


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    # Os tipos são criados explicitamente abaixo para permitir checkfirst. Sem
    # create_type=False, o PostgreSQL ENUM também tenta criá-los ao criar cada
    # tabela, causando DuplicateObject.
    line_status = postgresql.ENUM(
        *LINE_STATUSES, name="ingestao_linha_status", create_type=False
    )
    execution_status = postgresql.ENUM(
        *INGEST_STATUSES, name="ingestao_execucao_status", create_type=False
    )
    event_status = postgresql.ENUM(
        *LINE_STATUSES, name="ingestao_linha_evento_status", create_type=False
    )
    line_status.create(op.get_bind(), checkfirst=True)
    execution_status.create(op.get_bind(), checkfirst=True)
    event_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "ingestoes_linhas",
        sa.Column(
            "status",
            line_status,
            server_default=sa.text("'PENDENTE'"),
            nullable=False,
        ),
    )
    op.add_column("ingestoes_linhas", sa.Column("motivo", sa.Text(), nullable=True))
    op.add_column(
        "ingestoes_linhas", sa.Column("linha_duplicada_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_ingestoes_linhas_duplicada",
        "ingestoes_linhas",
        "ingestoes_linhas",
        ["linha_duplicada_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ingestoes_linhas_status", "ingestoes_linhas", ["status"], unique=False
    )
    op.execute(
        "UPDATE ingestoes_linhas SET status = CASE "
        "WHEN processada AND EXISTS (SELECT 1 FROM bolsas b "
        "WHERE b.id = ingestoes_linhas.bolsa_id AND b.is_conflict) "
        "THEN 'INSERIDA_CONFLITO'::ingestao_linha_status "
        "WHEN processada THEN 'INSERIDA'::ingestao_linha_status "
        "WHEN erro IS NOT NULL THEN 'ERRO'::ingestao_linha_status "
        "ELSE 'PENDENTE'::ingestao_linha_status END"
    )
    op.execute(
        "UPDATE ingestoes_linhas SET motivo = CASE "
        "WHEN status = 'INSERIDA_CONFLITO'::ingestao_linha_status "
        "THEN 'Bolsa armazenada para revisão por conflito de período.' "
        "WHEN status = 'ERRO'::ingestao_linha_status "
        "THEN 'Erro de processamento registrado antes da ativação da rastreabilidade.' "
        "ELSE NULL END"
    )
    for column in ("pesquisador_nome", "pesquisador_cidade", "territorio_identidade"):
        if column in _columns("ingestoes_linhas"):
            op.drop_column("ingestoes_linhas", column)

    op.create_table(
        "ingestoes_execucoes",
        sa.Column("ingestao_id", sa.UUID(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            execution_status,
            server_default=sa.text("'PROCESSANDO'"),
            nullable=False,
        ),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finalizada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["ingestao_id"], ["ingestoes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingestao_id", "numero", name="uq_ingestoes_execucoes_numero"),
    )
    op.create_index(
        "ix_ingestoes_execucoes_ingestao_id", "ingestoes_execucoes", ["ingestao_id"]
    )
    op.create_index(
        "ix_ingestoes_execucoes_status", "ingestoes_execucoes", ["status"]
    )

    op.create_table(
        "ingestoes_linhas_eventos",
        sa.Column("ingestao_linha_id", sa.UUID(), nullable=False),
        sa.Column("execucao_id", sa.UUID(), nullable=False),
        sa.Column("status", event_status, nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("bolsa_id", sa.UUID(), nullable=True),
        sa.Column("pesquisador_id", sa.UUID(), nullable=True),
        sa.Column("projeto_id", sa.UUID(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["bolsa_id"], ["bolsas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["execucao_id"], ["ingestoes_execucoes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingestao_linha_id"], ["ingestoes_linhas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pesquisador_id"], ["pesquisadores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("ingestao_linha_id", "execucao_id", "status", "criado_em"):
        op.create_index(
            f"ix_ingestoes_linhas_eventos_{column}",
            "ingestoes_linhas_eventos",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ("criado_em", "status", "execucao_id", "ingestao_linha_id"):
        op.drop_index(
            f"ix_ingestoes_linhas_eventos_{column}", table_name="ingestoes_linhas_eventos"
        )
    op.drop_table("ingestoes_linhas_eventos")
    op.drop_index("ix_ingestoes_execucoes_status", table_name="ingestoes_execucoes")
    op.drop_index("ix_ingestoes_execucoes_ingestao_id", table_name="ingestoes_execucoes")
    op.drop_table("ingestoes_execucoes")
    op.drop_index("ix_ingestoes_linhas_status", table_name="ingestoes_linhas")
    op.drop_constraint(
        "fk_ingestoes_linhas_duplicada", "ingestoes_linhas", type_="foreignkey"
    )
    op.drop_column("ingestoes_linhas", "linha_duplicada_id")
    op.drop_column("ingestoes_linhas", "motivo")
    op.drop_column("ingestoes_linhas", "status")
    existing_columns = _columns("ingestoes_linhas")
    for column in ("territorio_identidade", "pesquisador_cidade", "pesquisador_nome"):
        if column not in existing_columns:
            op.add_column(
                "ingestoes_linhas", sa.Column(column, sa.String(length=255), nullable=True)
            )
    postgresql.ENUM(name="ingestao_linha_evento_status").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="ingestao_execucao_status").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(name="ingestao_linha_status").drop(op.get_bind(), checkfirst=True)
