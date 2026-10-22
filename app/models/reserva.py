from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EstadoReserva
from app.models.forma_pagamento import FormaPagamento

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.veiculo import Veiculo


class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"))
    forma_pagamento_id: Mapped[int] = mapped_column(
        ForeignKey("formas_pagamento.id")
    )

    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)
    valor_total_centimos: Mapped[int] = mapped_column()
    estado: Mapped[EstadoReserva] = mapped_column(
        Enum(EstadoReserva), default=EstadoReserva.ATIVA
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    cliente: Mapped["Cliente"] = relationship(back_populates="reservas")
    veiculo: Mapped["Veiculo"] = relationship(back_populates="reservas")
    forma_pagamento: Mapped[FormaPagamento] = relationship()

    __table_args__ = (
        CheckConstraint(
            "data_fim > data_inicio", name="ck_reserva_datas_validas"
        ),
        Index(
            "ix_reserva_veiculo_datas",
            "veiculo_id",
            "data_inicio",
            "data_fim",
        ),
    )