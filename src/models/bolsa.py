from datetime import date

from sqlalchemy import Date, ForeignKey, String, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID
import uuid

from src.core.enums import ModalidadeBolsa
from src.models.base import Base


class Bolsa(Base):
    __tablename__ = "bolsas"

    quando_iniciou: Mapped[date | None] = mapped_column(Date, nullable=True)
    quando_terminou: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_saida_pesquisador: Mapped[date | None] = mapped_column(Date, nullable=True)
    modalidade: Mapped[ModalidadeBolsa | None] = mapped_column(
        SQLEnum(ModalidadeBolsa, native_enum=False, create_constraint=False, validate_strings=True),
        nullable=True
    )
    nome_curso: Mapped[str | None] = mapped_column(String(255), nullable=True)
    projeto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projetos.id"), nullable=False)
    instituicao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    pesquisador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pesquisadores.id"), nullable=False)

    projeto: Mapped["Projeto"] = relationship()
    instituicao: Mapped["Instituicao"] = relationship(back_populates="bolsas")
    pesquisador: Mapped["Pesquisador"] = relationship(back_populates="bolsas")

    __table_args__ = (
        ExcludeConstraint(
            ("pesquisador_id", "="),
            (func.daterange(quando_iniciou, quando_terminou, "[)"), "&&"),
            name="ex_bolsas_pesquisador_periodo",
            using="gist",
        ),
    )
