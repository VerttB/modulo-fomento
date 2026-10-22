"""guardar CEP de referência da bolsa

Revision ID: 0013_bolsa_cep_ref
Revises: 0012_ingest_linhas
Create Date: 2026-10-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0013_bolsa_cep_ref"
down_revision: str | None = "0012_ingest_linhas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bolsas", sa.Column("cep_referencia", sa.String(length=9), nullable=True))
    op.create_index(
        "ix_bolsas_pesquisador_inicio",
        "bolsas",
        ["pesquisador_id", "quando_iniciou"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_bolsas_pesquisador_inicio", table_name="bolsas")
    op.drop_column("bolsas", "cep_referencia")
