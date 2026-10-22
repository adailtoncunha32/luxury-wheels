"""Critérios 4 e 5: quando é que um veículo está (in)disponível."""

from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from app.models import Reserva
from app.models.enums import EstadoReserva
from app.services.disponibilidade import esta_operacional, ha_sobreposicao

HOJE = date(2026, 6, 15)


def carro(**alteracoes) -> Any:
    """Um 'veículo' falso: só tem os campos que esta_operacional precisa."""
    dados = {
        "em_manutencao": False,
        "data_ultima_inspecao": HOJE - timedelta(days=100),
        "data_proxima_revisao": HOJE + timedelta(days=30),
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def test_veiculo_em_dia_esta_operacional():
    assert esta_operacional(carro(), HOJE) is True


def test_inspecao_com_mais_de_um_ano_fica_indisponivel():
    assert esta_operacional(carro(data_ultima_inspecao=HOJE - timedelta(days=366)), HOJE) is False


def test_inspecao_com_exatamente_um_ano_ainda_vale():
    assert esta_operacional(carro(data_ultima_inspecao=HOJE - timedelta(days=365)), HOJE) is True


def test_revisao_atrasada_fica_indisponivel():
    assert esta_operacional(carro(data_proxima_revisao=HOJE - timedelta(days=1)), HOJE) is False


def test_revisao_marcada_para_hoje_ainda_vale():
    assert esta_operacional(carro(data_proxima_revisao=HOJE), HOJE) is True


def test_em_manutencao_fica_indisponivel():
    assert esta_operacional(carro(em_manutencao=True), HOJE) is False


def _reservar(db, veiculo, cliente, forma, inicio, fim, estado=EstadoReserva.ATIVA):
    reserva = Reserva(
        cliente_id=cliente.id,
        veiculo_id=veiculo.id,
        forma_pagamento_id=forma.id,
        data_inicio=inicio,
        data_fim=fim,
        valor_total_centimos=1,
        estado=estado,
    )
    db.add(reserva)
    db.commit()
    return reserva


def test_sobreposicao_parcial_e_detetada(db, veiculo, cliente, forma_pagamento):
    _reservar(db, veiculo, cliente, forma_pagamento, date(2026, 7, 1), date(2026, 7, 5))
    assert ha_sobreposicao(db, veiculo.id, date(2026, 7, 4), date(2026, 7, 8)) is True


def test_reserva_que_comeca_no_dia_da_devolucao_e_permitida(db, veiculo, cliente, forma_pagamento):
    _reservar(db, veiculo, cliente, forma_pagamento, date(2026, 7, 1), date(2026, 7, 5))
    assert ha_sobreposicao(db, veiculo.id, date(2026, 7, 5), date(2026, 7, 8)) is False


def test_reserva_cancelada_nao_bloqueia(db, veiculo, cliente, forma_pagamento):
    _reservar(
        db,
        veiculo,
        cliente,
        forma_pagamento,
        date(2026, 7, 1),
        date(2026, 7, 5),
        estado=EstadoReserva.CANCELADA,
    )
    assert ha_sobreposicao(db, veiculo.id, date(2026, 7, 2), date(2026, 7, 3)) is False


def test_ignorar_a_propria_reserva(db, veiculo, cliente, forma_pagamento):
    reserva = _reservar(db, veiculo, cliente, forma_pagamento, date(2026, 7, 1), date(2026, 7, 5))
    assert (
        ha_sobreposicao(db, veiculo.id, date(2026, 7, 2), date(2026, 7, 6), ignorar_reserva_id=reserva.id)
        is False
    )
