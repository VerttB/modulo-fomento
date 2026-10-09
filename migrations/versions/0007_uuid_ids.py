"""Muda IDs de integer para UUID em todas as tabelas.

Revision ID: 0007_uuid_ids
Revises: 0006_remove_pesquisador_cpf
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_uuid_ids"
down_revision: str | None = "0006_remove_pesquisador_cpf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Add UUID columns to all tables
    tables = [
        "instituicoes",
        "pesquisadores",
        "projetos",
        "areas_conhecimento",
        "departamentos",
        "unidades",
        "bolsas",
        "palavras_chave",
        "projetos_palavras_chave",
        "departamentos_unidades",
    ]

    for table in tables:
        op.add_column(table, sa.Column("uuid_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Populate UUID columns
    for table in tables:
        op.execute(f"UPDATE {table} SET uuid_id = uuid_generate_v4()")

    # Make UUID columns NOT NULL
    for table in tables:
        op.alter_column(table, "uuid_id", nullable=False)

    # Drop foreign key constraints
    op.drop_constraint("fk_unidades_departamento", "unidades", type_="foreignkey")
    op.drop_constraint("departamentos_instituicao_id_fkey", "departamentos", type_="foreignkey")
    op.drop_constraint("fk_departamentos_grande_area", "departamentos", type_="foreignkey")
    op.drop_constraint("bolsas_projeto_id_fkey", "bolsas", type="foreignkey")
    op.drop_constraint("bolsas_instituicao_id_fkey", "bolsas", type="foreignkey")
    op.drop_constraint("bolsas_pesquisador_id_fkey", "bolsas", type="foreignkey")
    op.drop_constraint("projetos_palavras_chave_projeto_id_fkey", "projetos_palavras_chave", type="foreignkey")
    op.drop_constraint("projetos_palavras_chave_palavra_chave_id_fkey", "projetos_palavras_chave", type="foreignkey")
    op.drop_constraint("departamentos_unidades_departamento_id_fkey", "departamentos_unidades", type="foreignkey")
    op.drop_constraint("departamentos_unidades_unidade_id_fkey", "departamentos_unidades", type="foreignkey")

    # Drop old PKs
    for table in tables:
        op.drop_constraint(f"{table}_pkey", table, type_="primarykey")

    # Rename uuid_id to id
    for table in tables:
        op.alter_column(table, "uuid_id", new_column_name="id")

    # Create new PKs
    for table in tables:
        op.create_primary_key(f"{table}_pkey", table, ["id"])

    # Recreate foreign keys
    op.create_foreign_key(
        "departamentos_instituicao_id_fkey", "departamentos", "instituicoes",
        ["instituicao_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_departamentos_grande_area", "departamentos", "areas_conhecimento",
        ["grande_area_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_unidades_departamento", "unidades", "departamentos",
        ["departamento_id"], ["id"]
    )
    op.create_foreign_key(
        "bolsas_projeto_id_fkey", "bolsas", "projetos",
        ["projeto_id"], ["id"]
    )
    op.create_foreign_key(
        "bolsas_instituicao_id_fkey", "bolsas", "instituicoes",
        ["instituicao_id"], ["id"]
    )
    op.create_foreign_key(
        "bolsas_pesquisador_id_fkey", "bolsas", "pesquisadores",
        ["pesquisador_id"], ["id"]
    )
    op.create_foreign_key(
        "projetos_palavras_chave_projeto_id_fkey", "projetos_palavras_chave", "projetos",
        ["projeto_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "projetos_palavras_chave_palavra_chave_id_fkey", "projetos_palavras_chave", "palavras_chave",
        ["palavra_chave_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "departamentos_unidades_departamento_id_fkey", "departamentos_unidades", "departamentos",
        ["departamento_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "departamentos_unidades_unidade_id_fkey", "departamentos_unidades", "unidades",
        ["unidade_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    # This is a destructive migration - downgrade not fully supported
    raise NotImplementedError("Downgrade not supported for UUID migration")