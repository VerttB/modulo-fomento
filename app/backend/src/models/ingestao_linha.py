import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import IngestaoLinhaStatus
from src.models.base import Base


class IngestaoLinha(Base):
    """Checkpoint de uma linha sem armazenar o CPF de origem."""

    __tablename__ = "ingestoes_linhas"

    ingestao_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestoes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    linha_origem: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[IngestaoLinhaStatus] = mapped_column(
        Enum(
            IngestaoLinhaStatus,
            name="ingestao_linha_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=IngestaoLinhaStatus.PENDENTE,
        server_default=IngestaoLinhaStatus.PENDENTE.value,
        index=True,
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    linha_duplicada_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "ingestoes_linhas.id",
            ondelete="SET NULL",
            name="fk_ingestoes_linhas_duplicada",
        ),
        nullable=True,
    )
    identificacao_concluida: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    lattes_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processada: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    bolsa_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bolsas.id", ondelete="SET NULL"), nullable=True
    )
    pesquisador_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pesquisadores.id", ondelete="SET NULL"), nullable=True
    )
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    ingestao: Mapped["Ingestao"] = relationship(back_populates="linhas")
    bolsa: Mapped["Bolsa | None"] = relationship()
    pesquisador: Mapped["Pesquisador | None"] = relationship()
    execucoes: Mapped[list["IngestaoLinhaEvento"]] = relationship(
        back_populates="linha", cascade="all, delete-orphan"
    )
    linha_duplicada: Mapped["IngestaoLinha | None"] = relationship(
        remote_side="IngestaoLinha.id"
    )

    __table_args__ = (
        UniqueConstraint("ingestao_id", "linha_origem", name="uq_ingestoes_linhas_origem"),
    )
