from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
import uuid

from src.models.associations import departamento_unidade
from src.models.base import Base


class Departamento(Base):
    __tablename__ = "departamentos"

    nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unidade: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(9), nullable=True)
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    grande_area_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("areas_conhecimento.id", name="fk_departamentos_grande_area"),
        nullable=True,
    )

    instituicao: Mapped["Instituicao"] = relationship(back_populates="departamentos")
    grande_area: Mapped["AreaConhecimento | None"] = relationship(back_populates="departamentos")

    unidades: Mapped[list["Unidade"]] = relationship(
        secondary=departamento_unidade, back_populates="departamentos"
    )

