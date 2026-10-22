import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import IngestaoLinhaStatus
from src.models.base import Base


class IngestaoLinhaEvento(Base):
    __tablename__ = "ingestoes_linhas_eventos"

    ingestao_linha_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestoes_linhas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execucao_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingestoes_execucoes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[IngestaoLinhaStatus] = mapped_column(
        Enum(
            IngestaoLinhaStatus,
            name="ingestao_linha_evento_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        index=True,
    )
    motivo: Mapped[str | None] = mapped_column(Text)
    bolsa_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bolsas.id", ondelete="SET NULL")
    )
    pesquisador_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pesquisadores.id", ondelete="SET NULL")
    )
    projeto_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projetos.id", ondelete="SET NULL")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    linha: Mapped["IngestaoLinha"] = relationship(back_populates="execucoes")
    execucao: Mapped["IngestaoExecucao"] = relationship(back_populates="eventos")
    bolsa: Mapped["Bolsa | None"] = relationship()
    pesquisador: Mapped["Pesquisador | None"] = relationship()
    projeto: Mapped["Projeto | None"] = relationship()

