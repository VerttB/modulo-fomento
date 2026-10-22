from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
import uuid

from src.models.base import Base
from src.core.enums import BolsaStatus


class Bolsa(Base):
    __tablename__ = "bolsas"

    quando_iniciou: Mapped[date | None] = mapped_column(Date, nullable=True)
    quando_terminou: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_saida_pesquisador: Mapped[date | None] = mapped_column(Date, nullable=True)
    cep_referencia: Mapped[str | None] = mapped_column(String(9), nullable=True)
    modalidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nome_curso: Mapped[str | None] = mapped_column(String(255), nullable=True)
    projeto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projetos.id"), nullable=False)
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    pesquisador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pesquisadores.id"), nullable=False)
    ingestao_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "ingestoes.id",
            ondelete="SET NULL",
            name="fk_bolsas_ingestao_id_ingestoes",
        ),
        nullable=True,
        index=True,
    )
    linha_origem: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_conflict: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    status: Mapped[BolsaStatus] = mapped_column(
        Enum(
            BolsaStatus,
            name="bolsa_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=BolsaStatus.REGULAR,
        server_default=BolsaStatus.REGULAR.value,
        index=True,
    )

    projeto: Mapped["Projeto"] = relationship()
    instituicao: Mapped["Instituicao"] = relationship(back_populates="bolsas")
    pesquisador: Mapped["Pesquisador"] = relationship(back_populates="bolsas")
    ingestao: Mapped["Ingestao | None"] = relationship(back_populates="bolsas")
    conflitos: Mapped[list["BolsaConflito"]] = relationship(
        foreign_keys="BolsaConflito.bolsa_em_conflito_id",
        back_populates="bolsa_em_conflito",
        cascade="all, delete-orphan",
    )
    relacionada_em_conflitos: Mapped[list["BolsaConflito"]] = relationship(
        foreign_keys="BolsaConflito.bolsa_relacionada_id",
        back_populates="bolsa_relacionada",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        ExcludeConstraint(
            ("pesquisador_id", "="),
            (func.daterange(quando_iniciou, quando_terminou, "[)"), "&&"),
            name="ex_bolsas_pesquisador_periodo",
            using="gist",
            where=status.in_([BolsaStatus.REGULAR, BolsaStatus.RESOLVIDA]),
        ),
        Index("ix_bolsas_pesquisador_inicio", "pesquisador_id", "quando_iniciou"),
    )
