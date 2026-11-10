from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class FotoPesquisador(Base):
    __tablename__ = "fotos_pesquisadores"

    pesquisador_id: Mapped[UUID] = mapped_column(
        ForeignKey("pesquisadores.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    pesquisador: Mapped["Pesquisador"] = relationship(back_populates="foto")
