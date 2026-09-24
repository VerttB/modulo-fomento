"""Schema inicial do módulo de fomento.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "instituicoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("cep", sa.String(length=9), nullable=False),
        sa.Column("sigla", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index(op.f("ix_instituicoes_sigla"), "instituicoes", ["sigla"], unique=True)

    op.create_table(
        "pesquisadores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lattes", sa.String(length=255), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pesquisadores_lattes"), "pesquisadores", ["lattes"], unique=True)
    op.create_index(op.f("ix_pesquisadores_nome"), "pesquisadores", ["nome"], unique=False)

    op.create_table(
        "projetos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("resumo", sa.Text(), nullable=False),
        sa.Column("grande_area", sa.String(length=255), nullable=False),
        sa.Column("subarea", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projetos_nome"), "projetos", ["nome"], unique=False)

    op.create_table(
        "areas_conhecimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("termo", sa.String(length=255), nullable=False),
        sa.Column("termo_normalizado", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("pai_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("tipo IN ('grande_area', 'area', 'subarea')", name="ck_areas_conhecimento_tipo"),
        sa.CheckConstraint(
            "(tipo = 'grande_area' AND pai_id IS NULL) OR "
            "(tipo IN ('area', 'subarea') AND pai_id IS NOT NULL)",
            name="ck_areas_conhecimento_pai",
        ),
        sa.ForeignKeyConstraint(["pai_id"], ["areas_conhecimento.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_areas_conhecimento_termo_normalizado"),
        "areas_conhecimento",
        ["termo_normalizado"],
        unique=False,
    )

    op.create_table(
        "palavras_chave",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("termo", sa.String(length=255), nullable=False),
        sa.Column("termo_normalizado", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_palavras_chave_termo_normalizado"),
        "palavras_chave",
        ["termo_normalizado"],
        unique=True,
    )

    op.create_table(
        "unidades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("cep", sa.String(length=9), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "bolsas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quando_iniciou", sa.Date(), nullable=False),
        sa.Column("quando_terminou", sa.Date(), nullable=True),
        sa.Column("data_saida_pesquisador", sa.Date(), nullable=True),
        sa.Column("modalidade", sa.String(length=100), nullable=False),
        sa.Column("nome_curso", sa.String(length=255), nullable=False),
        sa.Column("projeto_id", sa.Integer(), nullable=False),
        sa.Column("instituicao_id", sa.Integer(), nullable=False),
        sa.Column("pesquisador_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["instituicao_id"], ["instituicoes.id"]),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"]),
        sa.ForeignKeyConstraint(["pesquisador_id"], ["pesquisadores.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "ALTER TABLE bolsas ADD CONSTRAINT ex_bolsas_pesquisador_periodo "
        "EXCLUDE USING gist (pesquisador_id WITH =, "
        "daterange(quando_iniciou, data_saida_pesquisador, '[)') WITH &&)"
    )

    op.create_table(
        "departamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("unidade", sa.String(length=255), nullable=False),
        sa.Column("cep", sa.String(length=9), nullable=False),
        sa.Column("instituicao_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["instituicao_id"], ["instituicoes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "projetos_palavras_chave",
        sa.Column("projeto_id", sa.Integer(), nullable=False),
        sa.Column("palavra_chave_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["palavra_chave_id"], ["palavras_chave.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("projeto_id", "palavra_chave_id"),
    )


def downgrade() -> None:
    op.drop_table("projetos_palavras_chave")
    op.drop_table("departamentos")
    op.execute("ALTER TABLE bolsas DROP CONSTRAINT ex_bolsas_pesquisador_periodo")
    op.drop_table("bolsas")
    op.drop_table("unidades")
    op.drop_index(op.f("ix_palavras_chave_termo_normalizado"), table_name="palavras_chave")
    op.drop_table("palavras_chave")
    op.drop_index(op.f("ix_areas_conhecimento_termo_normalizado"), table_name="areas_conhecimento")
    op.drop_table("areas_conhecimento")
    op.drop_index(op.f("ix_projetos_nome"), table_name="projetos")
    op.drop_table("projetos")
    op.drop_index(op.f("ix_pesquisadores_nome"), table_name="pesquisadores")
    op.drop_index(op.f("ix_pesquisadores_lattes"), table_name="pesquisadores")
    op.drop_table("pesquisadores")
    op.drop_index(op.f("ix_instituicoes_sigla"), table_name="instituicoes")
    op.drop_table("instituicoes")
