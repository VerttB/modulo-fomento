"""Remove CPF column from pesquisadores table.

CPF não deve ser persistido no banco. A identificação do pesquisador
é feita via lattes (obtido da API externa).

Revision ID: 0006_remove_pesquisador_cpf
Revises: 0005_ingest_campos_opcionais
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_remove_pesquisador_cpf"
down_revision: str | None = "0005_ingest_campos_opcionais"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_pesquisadores_cpf", table_name="pesquisadores")
    op.drop_column("pesquisadores", "cpf")


def downgrade() -> None:
    op.add_column("pesquisadores", sa.Column("cpf", sa.String(length=11), nullable=True))
    op.create_index("ix_pesquisadores_cpf", "pesquisadores", ["cpf"], unique=True)