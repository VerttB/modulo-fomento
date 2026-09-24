from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str] = mapped_column(String(255), nullable=False)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    instituicao_id: Mapped[int] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)

    instituicao: Mapped["Instituicao"] = relationship(back_populates="departamentos")

    unidades: Mapped[list["Unidade"]] = relationship(back_populates="departamento")

