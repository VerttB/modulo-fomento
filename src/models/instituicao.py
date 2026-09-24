from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Instituicao(Base):
    __tablename__ = "instituicoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    sigla: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)

    departamentos: Mapped[list["Departamento"]] = relationship(back_populates="instituicao")
    bolsas: Mapped[list["Bolsa"]] = relationship(back_populates="instituicao")

