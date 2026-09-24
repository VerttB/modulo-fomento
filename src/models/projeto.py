from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.associations import projeto_palavra_chave
from src.models.base import Base


class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resumo: Mapped[str] = mapped_column(Text, nullable=False)
    grande_area: Mapped[str] = mapped_column(String(255), nullable=False)
    subarea: Mapped[str] = mapped_column(String(255), nullable=False)

    palavras_chave: Mapped[list["PalavraChave"]] = relationship(
        secondary=projeto_palavra_chave, back_populates="projetos"
    )
