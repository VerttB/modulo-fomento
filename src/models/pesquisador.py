from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import PesquisadorStatus
from src.models.base import Base


class Pesquisador(Base):
    __tablename__ = "pesquisadores"

    lattes: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    nome: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    cidade: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PesquisadorStatus] = mapped_column(
        Enum(
            PesquisadorStatus,
            name="pesquisador_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=PesquisadorStatus.PENDENTE,
        server_default=PesquisadorStatus.PENDENTE.value,
    )

    bolsas: Mapped[list["Bolsa"]] = relationship(back_populates="pesquisador")
