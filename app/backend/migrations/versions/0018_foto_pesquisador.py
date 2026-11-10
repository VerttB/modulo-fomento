"""Adiciona URL da foto vinculada ao pesquisador."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0018_foto_pesquisador"
down_revision: str | None = "5b645fb32224"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fotos_pesquisadores",
        sa.Column("pesquisador_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["pesquisador_id"], ["pesquisadores.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fotos_pesquisadores_pesquisador_id",
        "fotos_pesquisadores",
        ["pesquisador_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fotos_pesquisadores_pesquisador_id", table_name="fotos_pesquisadores"
    )
    op.drop_table("fotos_pesquisadores")
