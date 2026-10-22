"""Normaliza áreas de projeto e associa pesquisador a território."""

from collections.abc import Sequence
import re
import unicodedata
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_area_territorio_fk"
down_revision: str | None = "0008_area_territorio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def _area_id(connection, term: str | None, kind: str, parent_id):
    if not term or not term.strip():
        return parent_id
    normalized = _normalize(term)
    existing = connection.execute(
        sa.text(
            "SELECT id FROM areas_conhecimento "
            "WHERE tipo = :kind AND termo_normalizado = :normalized "
            "AND pai_id IS NOT DISTINCT FROM :parent_id LIMIT 1"
        ),
        {"kind": kind, "normalized": normalized, "parent_id": parent_id},
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    identifier = uuid.uuid4()
    connection.execute(
        sa.text(
            "INSERT INTO areas_conhecimento "
            "(id, termo, termo_normalizado, tipo, pai_id) "
            "VALUES (:id, :term, :normalized, :kind, :parent_id)"
        ),
        {
            "id": identifier,
            "term": term.strip(),
            "normalized": normalized,
            "kind": kind,
            "parent_id": parent_id,
        },
    )
    return identifier


def upgrade() -> None:
    connection = op.get_bind()
    op.add_column(
        "projetos",
        sa.Column("area_conhecimento_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    projects = connection.execute(
        sa.text("SELECT id, grande_area, area, subarea FROM projetos")
    ).mappings()
    for project in projects:
        grand_term = (project["grande_area"] or "").strip() or None
        area_term = (project["area"] or "").strip() or None
        subarea_term = (project["subarea"] or "").strip() or None
        if (area_term or subarea_term) and not grand_term:
            grand_term = "Grande área não informada"
        grand_id = _area_id(connection, grand_term, "grande_area", None)
        area_id = (
            _area_id(connection, area_term, "area", grand_id)
            if grand_id
            else None
        )
        if subarea_term and not area_id and grand_id:
            area_id = _area_id(connection, "Área não informada", "area", grand_id)
        subarea_id = (
            _area_id(connection, subarea_term, "subarea", area_id)
            if area_id
            else None
        )
        leaf_id = subarea_id if subarea_term and area_id else (
            area_id if area_term and grand_id else grand_id
        )
        connection.execute(
            sa.text(
                "UPDATE projetos SET area_conhecimento_id = :area_id WHERE id = :id"
            ),
            {"area_id": leaf_id, "id": project["id"]},
        )

    op.create_index(
        "ix_projetos_area_conhecimento_id", "projetos", ["area_conhecimento_id"]
    )
    op.create_foreign_key(
        "fk_projetos_area_conhecimento",
        "projetos",
        "areas_conhecimento",
        ["area_conhecimento_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_index("ix_projetos_area", table_name="projetos")
    op.drop_column("projetos", "grande_area")
    op.drop_column("projetos", "area")
    op.drop_column("projetos", "subarea")

    op.create_table(
        "territorios_identidade",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("nome_normalizado", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_territorios_identidade_nome",
        "territorios_identidade",
        ["nome"],
        unique=True,
    )
    op.create_index(
        "ix_territorios_identidade_nome_normalizado",
        "territorios_identidade",
        ["nome_normalizado"],
        unique=True,
    )
    op.add_column(
        "pesquisadores",
        sa.Column("territorio_identidade_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    territory_rows = connection.execute(
        sa.text(
            "SELECT DISTINCT territorio_identidade FROM pesquisadores "
            "WHERE territorio_identidade IS NOT NULL AND btrim(territorio_identidade) <> ''"
        )
    ).scalars()
    for name in territory_rows:
        normalized = _normalize(name)
        identifier = connection.execute(
            sa.text(
                "SELECT id FROM territorios_identidade "
                "WHERE nome_normalizado = :normalized LIMIT 1"
            ),
            {"normalized": normalized},
        ).scalar_one_or_none()
        if identifier is None:
            identifier = uuid.uuid4()
            connection.execute(
                sa.text(
                    "INSERT INTO territorios_identidade "
                    "(id, nome, nome_normalizado) VALUES (:id, :name, :normalized)"
                ),
                {"id": identifier, "name": name, "normalized": normalized},
            )
        connection.execute(
            sa.text(
                "UPDATE pesquisadores SET territorio_identidade_id = :id "
                "WHERE territorio_identidade = :name"
            ),
            {"id": identifier, "name": name},
        )
    op.create_index(
        "ix_pesquisadores_territorio_identidade_id",
        "pesquisadores",
        ["territorio_identidade_id"],
    )
    op.create_foreign_key(
        "fk_pesquisadores_territorio_identidade",
        "pesquisadores",
        "territorios_identidade",
        ["territorio_identidade_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_index("ix_pesquisadores_territorio_identidade", table_name="pesquisadores")
    op.drop_column("pesquisadores", "territorio_identidade")


def downgrade() -> None:
    raise NotImplementedError(
        "Migração de normalização preserva dados; não há downgrade automático seguro."
    )
