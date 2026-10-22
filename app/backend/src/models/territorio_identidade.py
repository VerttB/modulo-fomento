from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class TerritorioIdentidade(Base):
    __tablename__ = "territorios_identidade"

    nome: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    nome_normalizado: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    pesquisadores: Mapped[list["Pesquisador"]] = relationship(
        back_populates="territorio_identidade"
    )
