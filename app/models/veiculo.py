from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Categoria, TipoVeiculo, Transmissao

if TYPE_CHECKING:
    from app.models.reserva import Reserva


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    marca: Mapped[str] = mapped_column(String(50), index=True)
    modelo: Mapped[str] = mapped_column(String(50), index=True)
    categoria: Mapped[Categoria] = mapped_column(Enum(Categoria))
    transmissao: Mapped[Transmissao] = mapped_column(Enum(Transmissao))
    tipo: Mapped[TipoVeiculo] = mapped_column(Enum(TipoVeiculo))
    lugares: Mapped[int] = mapped_column()
    imagem: Mapped[str] = mapped_column(String(255))
    valor_diaria_centimos: Mapped[int] = mapped_column()  # 4550 = 45,50 €
    data_ultima_revisao: Mapped[date] = mapped_column(Date)
    data_proxima_revisao: Mapped[date] = mapped_column(Date)
    data_ultima_inspecao: Mapped[date] = mapped_column(Date)
    em_manutencao: Mapped[bool] = mapped_column(default=False)

    reservas: Mapped[list["Reserva"]] = relationship(back_populates="veiculo")
