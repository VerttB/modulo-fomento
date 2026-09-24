from sqlalchemy import Column, ForeignKey, Table

from src.models.base import Base

projeto_palavra_chave = Table(
    "projetos_palavras_chave",
    Base.metadata,
    Column("projeto_id", ForeignKey("projetos.id", ondelete="CASCADE"), primary_key=True),
    Column("palavra_chave_id", ForeignKey("palavras_chave.id", ondelete="CASCADE"), primary_key=True),
)
