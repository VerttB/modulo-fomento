from datetime import date

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Bolsa(Base):
    __tablename__ = "bolsas"

    id: Mapped[int] = mapped_column(primary_key=True)
    quando_iniciou: Mapped[date] = mapped_column(Date, nullable=False)
    quando_terminou: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_saida_pesquisador: Mapped[date | None] = mapped_column(Date, nullable=True)
    modalidade: Mapped[str] = mapped_column(String(100), nullable=False)
    nome_curso: Mapped[str] = mapped_column(String(255), nullable=False)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"), nullable=False)
    instituicao_id: Mapped[int] = mapped_column(ForeignKey("instituicoes.id"), nullable=False)
    pesquisador_id: Mapped[int] = mapped_column(ForeignKey("pesquisadores.id"), nullable=False)

    projeto: Mapped["Projeto"] = relationship()
    instituicao: Mapped["Instituicao"] = relationship(back_populates="bolsas")
    pesquisador: Mapped["Pesquisador"] = relationship(back_populates="bolsas")

    __table_args__ = (
        ExcludeConstraint(
            ("pesquisador_id", "="),
            (func.daterange(quando_iniciou, data_saida_pesquisador, "[)"), "&&"),
            name="ex_bolsas_pesquisador_periodo",
            using="gist",
        ),
    )
