"""fila ingestao hop

Revision ID: 5b645fb32224
Revises: 0017_projeto_search
Create Date: 2026-10-29 22:18:38.390147
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '5b645fb32224'
down_revision: str | None = '0017_projeto_search'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('ingestoes', sa.Column('enfileirada', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('ingestoes', 'enfileirada')
