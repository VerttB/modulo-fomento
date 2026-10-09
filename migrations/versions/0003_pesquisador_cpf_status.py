"""Adiciona CPF, cidade e status ao pesquisador.

Revision ID: 0003_pesquisador_cpf_status
Revises: 0001_initial_schema
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_pesquisador_cpf_status"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pesquisador_status = sa.Enum(
        "APROVADO",
        "PENDENTE",
        "REJEITADO",
        name="pesquisador_status",
    )
    pesquisador_status.create(op.get_bind(), checkfirst=True)
    op.add_column("pesquisadores", sa.Column("cpf", sa.String(length=11), nullable=True))
    op.add_column("pesquisadores", sa.Column("cidade", sa.String(length=255), nullable=True))
    op.add_column(
        "pesquisadores",
        sa.Column(
            "status",
            pesquisador_status,
            server_default=sa.text("'PENDENTE'"),
            nullable=False,
        ),
    )
    op.alter_column("pesquisadores", "lattes", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("pesquisadores", "nome", existing_type=sa.String(length=255), nullable=True)
    op.create_index("ix_pesquisadores_cpf", "pesquisadores", ["cpf"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_pesquisadores_cpf", table_name="pesquisadores")
    op.drop_column("pesquisadores", "status")
    sa.Enum(name="pesquisador_status").drop(op.get_bind(), checkfirst=True)
    op.drop_column("pesquisadores", "cidade")
    op.drop_column("pesquisadores", "cpf")
    op.alter_column("pesquisadores", "lattes", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("pesquisadores", "nome", existing_type=sa.String(length=255), nullable=False)
