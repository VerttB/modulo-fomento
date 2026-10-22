import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import BolsaConflitoStatus
from src.models.base import Base


class BolsaConflito(Base):
    __tablename__ = "bolsas_conflitos"

    bolsa_em_conflito_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bolsas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bolsa_relacionada_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bolsas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[BolsaConflitoStatus] = mapped_column(
        Enum(
            BolsaConflitoStatus,
            name="bolsa_conflito_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=BolsaConflitoStatus.PENDENTE,
        server_default=BolsaConflitoStatus.PENDENTE.value,
    )
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    bolsa_em_conflito: Mapped["Bolsa"] = relationship(
        foreign_keys=[bolsa_em_conflito_id], back_populates="conflitos"
    )
    bolsa_relacionada: Mapped["Bolsa"] = relationship(
        foreign_keys=[bolsa_relacionada_id], back_populates="relacionada_em_conflitos"
    )

    __table_args__ = (
        UniqueConstraint(
            "bolsa_em_conflito_id",
            "bolsa_relacionada_id",
            name="uq_bolsas_conflitos_par",
        ),
        CheckConstraint(
            "bolsa_em_conflito_id <> bolsa_relacionada_id",
            name="ck_bolsas_conflitos_distintas",
        ),
    )
