"""Cria visão materializada para indicadores de bolsas."""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_mv_bolsas_metricas"
down_revision: str | None = "0009_area_territorio_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW mv_bolsas_metricas AS
        SELECT
            EXTRACT(YEAR FROM b.quando_iniciou)::INTEGER AS ano_inicio,
            b.modalidade,
            i.id AS instituicao_id,
            i.nome AS instituicao_nome,
            i.sigla AS instituicao_sigla,
            p.cidade,
            ti.id AS territorio_identidade_id,
            ti.nome AS territorio_identidade,
            CASE selected.tipo
                WHEN 'grande_area' THEN selected.termo
                WHEN 'area' THEN parent.termo
                WHEN 'subarea' THEN root.termo
            END AS grande_area,
            CASE selected.tipo
                WHEN 'area' THEN selected.termo
                WHEN 'subarea' THEN parent.termo
            END AS area,
            CASE WHEN selected.tipo = 'subarea' THEN selected.termo END AS subarea,
            COUNT(*)::BIGINT AS quantidade
        FROM bolsas AS b
        JOIN projetos AS pr ON pr.id = b.projeto_id
        JOIN instituicoes AS i ON i.id = b.instituicao_id
        JOIN pesquisadores AS p ON p.id = b.pesquisador_id
        LEFT JOIN territorios_identidade AS ti
            ON ti.id = p.territorio_identidade_id
        LEFT JOIN areas_conhecimento AS selected
            ON selected.id = pr.area_conhecimento_id
        LEFT JOIN areas_conhecimento AS parent ON parent.id = selected.pai_id
        LEFT JOIN areas_conhecimento AS root ON root.id = parent.pai_id
        GROUP BY
            EXTRACT(YEAR FROM b.quando_iniciou)::INTEGER,
            b.modalidade, i.id, i.nome, i.sigla, p.cidade, ti.id, ti.nome,
            CASE selected.tipo
                WHEN 'grande_area' THEN selected.termo
                WHEN 'area' THEN parent.termo
                WHEN 'subarea' THEN root.termo
            END,
            CASE selected.tipo
                WHEN 'area' THEN selected.termo
                WHEN 'subarea' THEN parent.termo
            END,
            CASE WHEN selected.tipo = 'subarea' THEN selected.termo END
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_mv_bolsas_metricas_dims ON mv_bolsas_metricas "
        "(ano_inicio, modalidade, instituicao_id, instituicao_nome, instituicao_sigla, "
        "cidade, territorio_identidade_id, territorio_identidade, grande_area, area, subarea) "
        "NULLS NOT DISTINCT"
    )
    for name, column in (
        ("ix_mv_bolsas_metricas_ano", "ano_inicio"),
        ("ix_mv_bolsas_metricas_modalidade", "modalidade"),
        ("ix_mv_bolsas_metricas_instituicao", "instituicao_id"),
        ("ix_mv_bolsas_metricas_cidade", "cidade"),
        ("ix_mv_bolsas_metricas_grande_area", "grande_area"),
        ("ix_mv_bolsas_metricas_area", "area"),
        ("ix_mv_bolsas_metricas_territorio", "territorio_identidade_id"),
    ):
        op.create_index(name, "mv_bolsas_metricas", [column])


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_bolsas_metricas")
