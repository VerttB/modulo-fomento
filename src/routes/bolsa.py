from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.enums import ModalidadeBolsa
from src.schemas import BolsaCreate, BolsaRead, BolsaUpdate, PaginatedResponse, EstatisticasBolsas
from src.services.bolsa import (
    listar_bolsa,
    obter_bolsa,
    criar_bolsa,
    atualizar_bolsa,
    excluir_bolsa,
    estatisticas_bolsas,
)

router = APIRouter(prefix="/bolsas", tags=["Bolsas"])


@router.get("/", response_model=PaginatedResponse[BolsaRead])
def listar(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(30, ge=1, le=100, description="Tamanho da página"),
    area: str | None = Query(None, description="Filtrar por área/subárea"),
    grande_area: str | None = Query(None, description="Filtrar por grande área"),
    universidade: str | None = Query(None, description="Filtrar por universidade (nome ou sigla)"),
    cidade: str | None = Query(None, description="Filtrar por cidade do pesquisador"),
    modalidade: ModalidadeBolsa | None = Query(None, description="Filtrar por modalidade da bolsa"),
    ano_inicio: int | None = Query(None, ge=1900, le=2100, description="Ano de início (mínimo)"),
    ano_fim: int | None = Query(None, ge=1900, le=2100, description="Ano de fim (máximo)"),
    db: Session = Depends(get_db),
):
    items, total = listar_bolsa(
        db, page=page, size=size,
        area=area, grande_area=grande_area,
        universidade=universidade, cidade=cidade,
        modalidade=modalidade.value if modalidade else None, ano_inicio=ano_inicio, ano_fim=ano_fim,
    )
    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )


@router.get("/estatisticas", response_model=EstatisticasBolsas)
def estatisticas(db: Session = Depends(get_db)):
    """Retorna estatísticas consolidadas das bolsas."""
    return estatisticas_bolsas(db)


@router.get("/{resource_id}", response_model=BolsaRead)
def obter(resource_id: int, db: Session = Depends(get_db)):
    return obter_bolsa(db, resource_id)


@router.post("/", response_model=BolsaRead, status_code=status.HTTP_201_CREATED)
def criar(payload: BolsaCreate, db: Session = Depends(get_db)):
    return criar_bolsa(db, payload)


@router.patch("/{resource_id}", response_model=BolsaRead)
def atualizar(resource_id: int, payload: BolsaUpdate, db: Session = Depends(get_db)):
    return atualizar_bolsa(db, resource_id, payload)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(resource_id: int, db: Session = Depends(get_db)):
    excluir_bolsa(db, resource_id)
