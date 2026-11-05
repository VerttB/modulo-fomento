from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.atualizacao_pesquisadores import AtualizacaoPesquisadoresRequest, AtualizacaoPesquisadoresResultado
from src.services.atualizacao_pesquisadores import atualizar_pendentes


router = APIRouter(prefix="/administracao", tags=["Administração provisória"])


@router.post("/pesquisadores/atualizar-oda", response_model=AtualizacaoPesquisadoresResultado)
def atualizar_pesquisadores(
    payload: AtualizacaoPesquisadoresRequest,
    token: Annotated[str | None, Header(alias="X-Atualizacao-Token")] = None,
    db: Session = Depends(get_db),
):
    return atualizar_pendentes(db, payload, token)
