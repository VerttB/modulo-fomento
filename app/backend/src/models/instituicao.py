from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Instituicao(Base):
    __tablename__ = "instituicoes"

    nome: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    sigla: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)

    departamentos: Mapped[list["Departamento"]] = relationship(back_populates="instituicao")
    bolsas: Mapped[list["Bolsa"]] = relationship(back_populates="instituicao")

