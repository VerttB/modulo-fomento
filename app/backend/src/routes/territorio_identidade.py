from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.territorio_identidade import (
    listar_cidades_bahia,
    sincronizar_territorios_pesquisadores,
)

router = APIRouter(prefix="/territorios", tags=["Territórios de identidade"])


@router.get("/cidades")
def cidades():
    return listar_cidades_bahia()


@router.post("/sincronizar-pesquisadores")
def sincronizar_pesquisadores(db: Session = Depends(get_db)):
    return sincronizar_territorios_pesquisadores(db)
