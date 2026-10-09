"""Permite subarea vazia no projeto.

Revision ID: 0004_projeto_subarea_nullable
Revises: 0003_pesquisador_cpf_status
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_projeto_subarea_nullable"
down_revision: str | None = "0003_pesquisador_cpf_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "projetos",
        "subarea",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE projetos SET subarea = '' WHERE subarea IS NULL")
    op.alter_column(
        "projetos",
        "subarea",
        existing_type=sa.String(length=255),
        nullable=False,
    )
