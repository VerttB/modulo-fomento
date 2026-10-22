"""Converte as chaves primárias e estrangeiras para UUID.

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


ENTITY_TABLES = (
    "instituicoes",
    "pesquisadores",
    "projetos",
    "areas_conhecimento",
    "departamentos",
    "unidades",
    "bolsas",
    "palavras_chave",
)

# tabela, coluna FK, tabela referenciada, aceita NULL
FOREIGN_KEYS = (
    ("areas_conhecimento", "pai_id", "areas_conhecimento", True),
    ("departamentos", "instituicao_id", "instituicoes", False),
    ("departamentos", "grande_area_id", "areas_conhecimento", True),
    ("bolsas", "projeto_id", "projetos", False),
    ("bolsas", "instituicao_id", "instituicoes", False),
    ("bolsas", "pesquisador_id", "pesquisadores", False),
    ("projetos_palavras_chave", "projeto_id", "projetos", False),
    ("projetos_palavras_chave", "palavra_chave_id", "palavras_chave", False),
    ("departamentos_unidades", "departamento_id", "departamentos", False),
    ("departamentos_unidades", "unidade_id", "unidades", False),
)

ASSOCIATION_TABLES = (
    "projetos_palavras_chave",
    "departamentos_unidades",
)


def _populate_uuid_columns() -> None:
    for table_name in ENTITY_TABLES:
        op.add_column(
            table_name,
            sa.Column("uuid_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.execute(sa.text(f'UPDATE "{table_name}" SET uuid_id = uuid_generate_v4()'))
        op.alter_column(table_name, "uuid_id", nullable=False)

    for table_name, column_name, parent_table, nullable in FOREIGN_KEYS:
        temporary_column = f"uuid_{column_name}"
        op.add_column(
            table_name,
            sa.Column(temporary_column, postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.execute(
            sa.text(
                f'UPDATE "{table_name}" AS child '
                f'SET "{temporary_column}" = parent.uuid_id '
                f'FROM "{parent_table}" AS parent '
                f'WHERE child."{column_name}" = parent.id'
            )
        )
        if not nullable:
            op.alter_column(table_name, temporary_column, nullable=False)


def _drop_constraints() -> None:
    foreign_keys = (
        ("areas_conhecimento_pai_id_fkey", "areas_conhecimento"),
        ("departamentos_instituicao_id_fkey", "departamentos"),
        ("fk_departamentos_grande_area", "departamentos"),
        ("bolsas_projeto_id_fkey", "bolsas"),
        ("bolsas_instituicao_id_fkey", "bolsas"),
        ("bolsas_pesquisador_id_fkey", "bolsas"),
        ("projetos_palavras_chave_projeto_id_fkey", "projetos_palavras_chave"),
        ("projetos_palavras_chave_palavra_chave_id_fkey", "projetos_palavras_chave"),
        ("departamentos_unidades_departamento_id_fkey", "departamentos_unidades"),
        ("departamentos_unidades_unidade_id_fkey", "departamentos_unidades"),
    )
    for name, table_name in foreign_keys:
        op.drop_constraint(name, table_name, type_="foreignkey")

    # Constraints dependentes saem antes das chaves primárias.
    for table_name in (*ENTITY_TABLES, *ASSOCIATION_TABLES):
        op.drop_constraint(f"{table_name}_pkey", table_name, type_="primary")

    # A restrição usa pesquisador_id, que será substituída por UUID.
    op.execute(
        "ALTER TABLE bolsas DROP CONSTRAINT IF EXISTS "
        "ex_bolsas_pesquisador_periodo"
    )


def _replace_columns() -> None:
    for table_name in ENTITY_TABLES:
        op.drop_column(table_name, "id")
        op.alter_column(table_name, "uuid_id", new_column_name="id")

    for table_name, column_name, _parent_table, _nullable in FOREIGN_KEYS:
        temporary_column = f"uuid_{column_name}"
        op.drop_column(table_name, column_name)
        op.alter_column(table_name, temporary_column, new_column_name=column_name)


def _create_primary_keys() -> None:
    for table_name in ENTITY_TABLES:
        op.create_primary_key(f"{table_name}_pkey", table_name, ["id"])

    op.create_primary_key(
        "projetos_palavras_chave_pkey",
        "projetos_palavras_chave",
        ["projeto_id", "palavra_chave_id"],
    )
    op.create_primary_key(
        "departamentos_unidades_pkey",
        "departamentos_unidades",
        ["departamento_id", "unidade_id"],
    )


def _create_foreign_keys() -> None:
    op.create_foreign_key(
        "areas_conhecimento_pai_id_fkey",
        "areas_conhecimento",
        "areas_conhecimento",
        ["pai_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "departamentos_instituicao_id_fkey",
        "departamentos",
        "instituicoes",
        ["instituicao_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_departamentos_grande_area",
        "departamentos",
        "areas_conhecimento",
        ["grande_area_id"],
        ["id"],
    )
    op.create_foreign_key(
        "bolsas_projeto_id_fkey", "bolsas", "projetos", ["projeto_id"], ["id"]
    )
    op.create_foreign_key(
        "bolsas_instituicao_id_fkey",
        "bolsas",
        "instituicoes",
        ["instituicao_id"],
        ["id"],
    )
    op.create_foreign_key(
        "bolsas_pesquisador_id_fkey",
        "bolsas",
        "pesquisadores",
        ["pesquisador_id"],
        ["id"],
    )
    op.create_foreign_key(
        "projetos_palavras_chave_projeto_id_fkey",
        "projetos_palavras_chave",
        "projetos",
        ["projeto_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "projetos_palavras_chave_palavra_chave_id_fkey",
        "projetos_palavras_chave",
        "palavras_chave",
        ["palavra_chave_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "departamentos_unidades_departamento_id_fkey",
        "departamentos_unidades",
        "departamentos",
        ["departamento_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "departamentos_unidades_unidade_id_fkey",
        "departamentos_unidades",
        "unidades",
        ["unidade_id"],
        ["id"],
        ondelete="CASCADE",
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    _populate_uuid_columns()
    _drop_constraints()
    _replace_columns()
    _create_primary_keys()
    _create_foreign_keys()
    op.execute(
        "ALTER TABLE bolsas ADD CONSTRAINT ex_bolsas_pesquisador_periodo "
        "EXCLUDE USING gist (pesquisador_id WITH =, "
        "daterange(quando_iniciou, quando_terminou, '[)') WITH &&)"
    )


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for UUID migration")
