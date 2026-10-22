from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base

projeto_palavra_chave = Table(
    "projetos_palavras_chave",
    Base.metadata,
    Column("projeto_id", UUID(as_uuid=True), ForeignKey("projetos.id", ondelete="CASCADE"), primary_key=True),
    Column("palavra_chave_id", UUID(as_uuid=True), ForeignKey("palavras_chave.id", ondelete="CASCADE"), primary_key=True),
)

departamento_unidade = Table(
    "departamentos_unidades",
    Base.metadata,
    Column("departamento_id", UUID(as_uuid=True), ForeignKey("departamentos.id", ondelete="CASCADE"), primary_key=True),
    Column("unidade_id", UUID(as_uuid=True), ForeignKey("unidades.id", ondelete="CASCADE"), primary_key=True),
)
