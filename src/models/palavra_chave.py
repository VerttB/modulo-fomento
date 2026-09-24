from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.associations import projeto_palavra_chave
from src.models.base import Base


class PalavraChave(Base):
    __tablename__ = "palavras_chave"

    id: Mapped[int] = mapped_column(primary_key=True)
    termo: Mapped[str] = mapped_column(String(255), nullable=False)
    termo_normalizado: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    projetos: Mapped[list["Projeto"]] = relationship(
        secondary=projeto_palavra_chave, back_populates="palavras_chave"
    )
