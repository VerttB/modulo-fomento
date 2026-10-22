import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import IngestaoStatus
from src.models.base import Base


class IngestaoExecucao(Base):
    __tablename__ = "ingestoes_execucoes"

    ingestao_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestoes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[IngestaoStatus] = mapped_column(
        Enum(
            IngestaoStatus,
            name="ingestao_execucao_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=IngestaoStatus.PROCESSANDO,
        server_default=IngestaoStatus.PROCESSANDO.value,
        index=True,
    )
    iniciada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erro: Mapped[str | None] = mapped_column(Text)

    ingestao: Mapped["Ingestao"] = relationship(back_populates="execucoes")
    eventos: Mapped[list["IngestaoLinhaEvento"]] = relationship(
        back_populates="execucao", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("ingestao_id", "numero", name="uq_ingestoes_execucoes_numero"),
    )

