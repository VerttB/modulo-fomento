from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamentos.id", name="fk_unidades_departamento"), nullable=False)

    departamento: Mapped["Departamento"] = relationship(back_populates="unidades")
