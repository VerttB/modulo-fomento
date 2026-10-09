"""Permite campos vazios vindos do documento de ingestão.

Revision ID: 0005_ingest_campos_opcionais
Revises: 0004_projeto_subarea_nullable
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_ingest_campos_opcionais"
down_revision: str | None = "0004_projeto_subarea_nullable"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


COLUNAS: tuple[tuple[str, str, sa.types.TypeEngine], ...] = (
    ("projetos", "nome", sa.String(length=255)),
    ("projetos", "resumo", sa.Text()),
    ("projetos", "grande_area", sa.String(length=255)),
    ("instituicoes", "nome", sa.String(length=255)),
    ("instituicoes", "cep", sa.String(length=9)),
    ("instituicoes", "sigla", sa.String(length=32)),
    ("departamentos", "nome", sa.String(length=255)),
    ("departamentos", "unidade", sa.String(length=255)),
    ("departamentos", "cep", sa.String(length=9)),
    ("unidades", "nome", sa.String(length=255)),
    ("unidades", "cep", sa.String(length=9)),
    ("bolsas", "quando_iniciou", sa.Date()),
    ("bolsas", "modalidade", sa.String(length=100)),
    ("bolsas", "nome_curso", sa.String(length=255)),
)


def upgrade() -> None:
    for tabela, coluna, tipo in COLUNAS:
        op.alter_column(tabela, coluna, existing_type=tipo, nullable=True)


def downgrade() -> None:
    for tabela, coluna, tipo in COLUNAS:
        if (tabela, coluna) == ("bolsas", "quando_iniciou"):
            # Sem valor padrão sensato para data: o banco recusa
            # a reversão enquanto existirem bolsas sem data inicial.
            op.alter_column(tabela, coluna, existing_type=tipo, nullable=False)
            continue
        op.execute(sa.text(f"UPDATE {tabela} SET {coluna} = '' WHERE {coluna} IS NULL"))
        op.alter_column(tabela, coluna, existing_type=tipo, nullable=False)
