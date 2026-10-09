from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.associations import departamento_unidade
from src.models.base import Base


class Unidade(Base):
    __tablename__ = "unidades"

    nome: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)

    departamentos: Mapped[list["Departamento"]] = relationship(
        secondary=departamento_unidade, back_populates="unidades"
    )
