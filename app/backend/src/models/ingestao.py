import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import IngestaoStatus
from src.models.base import Base


class Ingestao(Base):
    __tablename__ = "ingestoes"

    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade_linhas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    arquivo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    arquivo_original_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    arquivo_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[IngestaoStatus] = mapped_column(
        Enum(
            IngestaoStatus,
            name="ingestao_status",
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
    finalizada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    linhas_processadas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    linhas_duplicadas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    linhas_ignoradas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    bolsas_conflitantes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    pesquisadores_consultados: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    pesquisadores_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    bolsas: Mapped[list["Bolsa"]] = relationship(back_populates="ingestao")
    linhas: Mapped[list["IngestaoLinha"]] = relationship(
        back_populates="ingestao", cascade="all, delete-orphan"
    )
    execucoes: Mapped[list["IngestaoExecucao"]] = relationship(
        back_populates="ingestao", cascade="all, delete-orphan"
    )
