from sqlalchemy import CheckConstraint, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import AreaConhecimentoTipo
from src.models.base import Base


class AreaConhecimento(Base):
    __tablename__ = "areas_conhecimento"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('grande_area', 'area', 'subarea')",
            name="ck_areas_conhecimento_tipo",
        ),
        CheckConstraint(
            "(tipo = 'grande_area' AND pai_id IS NULL) OR "
            "(tipo IN ('area', 'subarea') AND pai_id IS NOT NULL)",
            name="ck_areas_conhecimento_pai",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    termo: Mapped[str] = mapped_column(String(255), nullable=False)
    termo_normalizado: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo: Mapped[AreaConhecimentoTipo] = mapped_column(
        Enum(AreaConhecimentoTipo, native_enum=False, create_constraint=False), nullable=False
    )
    pai_id: Mapped[int | None] = mapped_column(
        ForeignKey("areas_conhecimento.id", ondelete="RESTRICT"), nullable=True
    )

    pai: Mapped["AreaConhecimento | None"] = relationship(
        remote_side="AreaConhecimento.id", back_populates="filhas"
    )
    filhas: Mapped[list["AreaConhecimento"]] = relationship(back_populates="pai")
