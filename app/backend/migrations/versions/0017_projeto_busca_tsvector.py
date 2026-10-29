"""Adiciona busca textual de projetos com tsvector e GIN."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0017_projeto_search"
down_revision: str | None = "0016_busca_unaccent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CONFIG = "public.portuguese_unaccent"
SEARCH_VECTOR = (
    f"setweight(to_tsvector('{CONFIG}'::regconfig, coalesce(nome, '')), 'A') || "
    f"setweight(to_tsvector('{CONFIG}'::regconfig, coalesce(resumo, '')), 'B')"
)


def upgrade() -> None:
    op.execute(
        f"CREATE TEXT SEARCH CONFIGURATION {CONFIG} "
        "(COPY = pg_catalog.portuguese)"
    )
    op.execute(
        f"ALTER TEXT SEARCH CONFIGURATION {CONFIG} "
        "ALTER MAPPING FOR hword, hword_part, word "
        "WITH public.unaccent, pg_catalog.portuguese_stem"
    )
    op.add_column(
        "projetos",
        sa.Column(
            "busca",
            postgresql.TSVECTOR(),
            sa.Computed(SEARCH_VECTOR, persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_projetos_busca_gin",
        "projetos",
        ["busca"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_projetos_busca_gin", table_name="projetos")
    op.drop_column("projetos", "busca")
    op.execute(f"DROP TEXT SEARCH CONFIGURATION {CONFIG}")
