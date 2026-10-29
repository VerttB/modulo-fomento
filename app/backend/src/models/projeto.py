import uuid

from sqlalchemy import Computed, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.associations import projeto_palavra_chave
from src.models.base import Base
from src.core.search import PORTUGUESE_SEARCH_CONFIG


class Projeto(Base):
    __tablename__ = "projetos"
    __table_args__ = (
        Index("ix_projetos_busca_gin", "busca", postgresql_using="gin"),
    )

    nome: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    resumo: Mapped[str | None] = mapped_column(Text, nullable=True)
    busca: Mapped[object] = mapped_column(
        TSVECTOR,
        Computed(
            f"setweight(to_tsvector('{PORTUGUESE_SEARCH_CONFIG}'::regconfig, "
            "coalesce(nome, '')), 'A') || "
            f"setweight(to_tsvector('{PORTUGUESE_SEARCH_CONFIG}'::regconfig, "
            "coalesce(resumo, '')), 'B')",
            persisted=True,
        ),
        nullable=True,
    )
    area_conhecimento_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("areas_conhecimento.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    area_conhecimento: Mapped["AreaConhecimento | None"] = relationship()

    palavras_chave: Mapped[list["PalavraChave"]] = relationship(
        secondary=projeto_palavra_chave, back_populates="projetos"
    )
