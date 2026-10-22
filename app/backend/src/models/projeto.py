import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.associations import projeto_palavra_chave
from src.models.base import Base


class Projeto(Base):
    __tablename__ = "projetos"

    nome: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_conhecimento_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("areas_conhecimento.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    area_conhecimento: Mapped["AreaConhecimento | None"] = relationship()

    palavras_chave: Mapped[list["PalavraChave"]] = relationship(
        secondary=projeto_palavra_chave, back_populates="projetos"
    )
