"""Habilita comparação de texto sem distinção de acentos."""

from collections.abc import Sequence

from alembic import op


revision: str = "0016_busca_unaccent"
down_revision: str | None = "0015_ingest_trace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    # A extensão pode ser usada por consultas fora deste sistema.
    pass
