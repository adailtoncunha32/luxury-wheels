"""Pesquisa de veículos com filtros (requisito 2)."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Veiculo
from app.models.enums import Categoria, TipoVeiculo, Transmissao
from app.services.disponibilidade import esta_disponivel

# Faixas de lugares pedidas no enunciado: 1-4, 5-6, mais de 7. None = sem limite máximo.
FAIXAS_LUGARES: dict[str, tuple[int, int | None]] = {
    "1-4": (1, 4),
    "5-6": (5, 6),
    "7+": (7, None),
}


@dataclass
class FiltrosPesquisa:
    inicio: date
    fim: date
    texto: str | None = None
    categoria: Categoria | None = None
    transmissao: Transmissao | None = None
    tipo: TipoVeiculo | None = None
    preco_max_centimos: int | None = None
    lugares: str | None = None


def pesquisar_veiculos(db: Session, filtros: FiltrosPesquisa, hoje: date) -> list[Veiculo]:
    consulta = select(Veiculo)

    if filtros.texto:
        termo = f"%{filtros.texto}%"
        consulta = consulta.where(or_(Veiculo.marca.ilike(termo), Veiculo.modelo.ilike(termo)))
    if filtros.categoria:
        consulta = consulta.where(Veiculo.categoria == filtros.categoria)
    if filtros.transmissao:
        consulta = consulta.where(Veiculo.transmissao == filtros.transmissao)
    if filtros.tipo:
        consulta = consulta.where(Veiculo.tipo == filtros.tipo)
    if filtros.preco_max_centimos is not None:
        consulta = consulta.where(Veiculo.valor_diaria_centimos <= filtros.preco_max_centimos)
    if filtros.lugares in FAIXAS_LUGARES:
        minimo, maximo = FAIXAS_LUGARES[filtros.lugares]
        consulta = consulta.where(Veiculo.lugares >= minimo)
        if maximo is not None:
            consulta = consulta.where(Veiculo.lugares <= maximo)

    veiculos = db.scalars(consulta.order_by(Veiculo.valor_diaria_centimos)).all()
    # Filtros "de BD" acima; regras de negócio (inspeção, revisão, reservas) em Python abaixo.
    return [v for v in veiculos if esta_disponivel(db, v, filtros.inicio, filtros.fim, hoje)]
