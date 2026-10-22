"""Adiciona dimensão área e território de identidade para análise."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_area_territorio"
down_revision: str | None = "0007_uuid_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projetos", sa.Column("area", sa.String(255), nullable=True))
    op.create_index("ix_projetos_area", "projetos", ["area"])
    op.add_column(
        "pesquisadores", sa.Column("territorio_identidade", sa.String(255), nullable=True)
    )
    op.create_index(
        "ix_pesquisadores_territorio_identidade",
        "pesquisadores",
        ["territorio_identidade"],
    )


def downgrade() -> None:
    op.drop_index("ix_pesquisadores_territorio_identidade", table_name="pesquisadores")
    op.drop_column("pesquisadores", "territorio_identidade")
    op.drop_index("ix_projetos_area", table_name="projetos")
    op.drop_column("projetos", "area")
