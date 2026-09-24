"""Vincula cada unidade a um departamento.

Revision ID: 0002_unidades_departamento
Revises: 0001_initial_schema
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_unidades_departamento"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "unidades",
        sa.Column("departamento_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "fk_unidades_departamento",
        "unidades",
        "departamentos",
        ["departamento_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_unidades_departamento", "unidades", type_="foreignkey")
    op.drop_column("unidades", "departamento_id")
