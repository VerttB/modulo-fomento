from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, Field


class Paginacao(BaseModel):
    page: int = Field(default=1, ge=1, description="Número da página")
    size: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Quantidade de registros por página",
    )


PaginacaoQuery = Annotated[Paginacao, Depends()]
