"""Regras de disponibilidade dos veículos (critérios técnicos 4 e 5 do enunciado).

Este ficheiro não sabe nada de HTTP nem de HTML: só recebe dados e devolve True/False.
Por isso é fácil de testar (ver tests/test_disponibilidade.py).
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Reserva, Veiculo

VALIDADE_INSPECAO = timedelta(days=365)


def esta_operacional(veiculo: Veiculo, hoje: date) -> bool:
    """Critério 5: o veículo pode circular? (manutenção, inspeção e revisão em dia)."""
    if veiculo.em_manutencao:
        return False
    if hoje - veiculo.data_ultima_inspecao > VALIDADE_INSPECAO:
        return False
    if veiculo.data_proxima_revisao < hoje:
        return False
    return True
    raise NotImplementedError


def ha_sobreposicao(
    db: Session,
    veiculo_id: int,
    inicio: date,
    fim: date,
    ignorar_reserva_id: int | None = None,
) -> bool:
    """Critério 4: já existe uma reserva ATIVA deste veículo que choque com [inicio, fim)?"""
    consulta = select(Reserva.id).where(
        Reserva.veiculo_id == veiculo_id,
        Reserva.estado == "ATIVA",
        Reserva.data_inicio < fim,
        Reserva.data_fim > inicio,
    )
    if ignorar_reserva_id is not None:
        consulta = consulta.where(Reserva.id != ignorar_reserva_id)
    return db.scalar(consulta.limit(1)) is not None
    raise NotImplementedError


def esta_disponivel(db: Session, veiculo: Veiculo, inicio: date, fim: date, hoje: date) -> bool:
    """Junta as duas regras: pode circular E está livre nessas datas."""
    return esta_operacional(veiculo, hoje) and not ha_sobreposicao(db, veiculo.id, inicio, fim)
