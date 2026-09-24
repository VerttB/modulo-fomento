from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Pesquisador(Base):
    __tablename__ = "pesquisadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    lattes: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    bolsas: Mapped[list["Bolsa"]] = relationship(back_populates="pesquisador")
