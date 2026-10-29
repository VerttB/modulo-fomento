from pydantic import BaseModel, Field
from fastapi import Query


class BolsaFiltros(BaseModel):
    """Filtros compartilhados pelas consultas, estatísticas e exportações de bolsas."""

    area: list[str] | None = Field(default=None, description="Uma ou mais áreas")
    grande_area: list[str] | None = Field(
        default=None, description="Uma ou mais grandes áreas"
    )
    instituicao: list[str] | None = Field(
        default=None, description="Uma ou mais instituições, por nome ou sigla"
    )
    cidade: list[str] | None = Field(
        default=None, description="Um ou mais municípios dos pesquisadores"
    )
    territorio_identidade: list[str] | None = Field(
        default=None, description="Um ou mais territórios de identidade"
    )
    modalidade: list[str] | None = Field(
        default=None, description="Uma ou mais modalidades"
    )
    ano_inicio: int | None = Field(default=None, ge=1900, le=2100)
    ano_fim: int | None = Field(default=None, ge=1900, le=2100)


def filtros_bolsa_query(
    area: list[str] | None = Query(default=None, description="Uma ou mais áreas"),
    grande_area: list[str] | None = Query(
        default=None, description="Uma ou mais grandes áreas"
    ),
    instituicao: list[str] | None = Query(
        default=None, description="Uma ou mais instituições, por nome ou sigla"
    ),
    cidade: list[str] | None = Query(
        default=None, description="Um ou mais municípios dos pesquisadores"
    ),
    territorio_identidade: list[str] | None = Query(
        default=None, description="Um ou mais territórios de identidade"
    ),
    modalidade: list[str] | None = Query(
        default=None, description="Uma ou mais modalidades"
    ),
    ano_inicio: int | None = Query(default=None, ge=1900, le=2100),
    ano_fim: int | None = Query(default=None, ge=1900, le=2100),
) -> BolsaFiltros:
    return BolsaFiltros(
        area=area,
        grande_area=grande_area,
        instituicao=instituicao,
        cidade=cidade,
        territorio_identidade=territorio_identidade,
        modalidade=modalidade,
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
    )
