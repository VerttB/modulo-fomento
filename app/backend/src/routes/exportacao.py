from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.bolsa import BolsaFiltros, filtros_bolsa_query
from src.services.exportacao_bolsistas import (
    ArquivoExportacao,
    exportar_registros_bolsistas,
    exportar_resumo_bolsistas,
)


router = APIRouter(prefix="/exportacoes/bolsistas", tags=["Exportações"])
Recorte = Literal["territorio", "cidade", "instituicao"]
ACCEPT_DESCRIPTION = (
    "Formato: text/csv, application/vnd.openxmlformats-officedocument."
    "spreadsheetml.sheet ou application/json."
)


def _resposta(arquivo: ArquivoExportacao) -> StreamingResponse:
    return StreamingResponse(
        arquivo.conteudo,
        media_type=arquivo.media_type,
        headers={"Content-Disposition": f'attachment; filename="{arquivo.filename}"'},
    )


@router.get("/resumo", response_class=StreamingResponse)
def exportar_resumo(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    recorte: list[Recorte] | None = Query(None),
    accept: Annotated[
        str | None,
        Header(description=ACCEPT_DESCRIPTION),
    ] = None,
    db: Session = Depends(get_db),
):
    arquivo = exportar_resumo_bolsistas(
        db,
        filtros,
        recortes=recorte,
        accept=accept,
    )
    return _resposta(arquivo)


@router.get("/registros", response_class=StreamingResponse)
def exportar_registros(
    filtros: Annotated[BolsaFiltros, Depends(filtros_bolsa_query)],
    termo: str | None = Query(None, max_length=150),
    accept: Annotated[
        str | None,
        Header(description=ACCEPT_DESCRIPTION),
    ] = None,
    db: Session = Depends(get_db),
):
    arquivo = exportar_registros_bolsistas(
        db,
        filtros,
        termo=termo,
        accept=accept,
    )
    return _resposta(arquivo)
