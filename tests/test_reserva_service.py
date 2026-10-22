"""Regras do balcão de reservas: total, criar, alterar, cancelar e anti-IDOR."""

from datetime import date, timedelta

import pytest

from app.models.enums import EstadoReserva
from app.services.reserva_service import (
    ErroReserva,
    alterar_datas,
    calcular_total,
    cancelar_reserva,
    criar_reserva,
    obter_reserva_do_cliente,
)
from tests.conftest import HOJE, novo_cliente, novo_veiculo

AMANHA = HOJE + timedelta(days=1)


def test_total_e_diaria_vezes_dias():
    assert calcular_total(5000, date(2026, 1, 1), date(2026, 1, 4)) == 15000  # 3 dias x 50 €


def test_total_com_datas_invalidas_da_erro():
    with pytest.raises(ErroReserva):
        calcular_total(5000, date(2026, 1, 4), date(2026, 1, 4))


def test_criar_reserva_guarda_o_total(db, veiculo, cliente, forma_pagamento):
    reserva = criar_reserva(
        db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=3), HOJE
    )
    assert reserva.valor_total_centimos == 15000
    assert reserva.estado == EstadoReserva.ATIVA


def test_nao_reserva_no_passado(db, veiculo, cliente, forma_pagamento):
    with pytest.raises(ErroReserva):
        criar_reserva(db, cliente.id, veiculo.id, forma_pagamento.id, HOJE - timedelta(days=1), AMANHA, HOJE)


def test_veiculo_reservado_deixa_de_estar_disponivel(db, veiculo, cliente, forma_pagamento):
    criar_reserva(db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=3), HOJE)
    outro = novo_cliente(db, "rui@exemplo.pt")
    with pytest.raises(ErroReserva):
        criar_reserva(
            db,
            outro.id,
            veiculo.id,
            forma_pagamento.id,
            AMANHA + timedelta(days=1),
            AMANHA + timedelta(days=2),
            HOJE,
        )


def test_nao_reserva_veiculo_com_inspecao_vencida(db, cliente, forma_pagamento):
    velho = novo_veiculo(db, data_ultima_inspecao=HOJE - timedelta(days=400))
    with pytest.raises(ErroReserva):
        criar_reserva(db, cliente.id, velho.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=1), HOJE)


def test_alterar_datas_recalcula_total(db, veiculo, cliente, forma_pagamento):
    reserva = criar_reserva(
        db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=2), HOJE
    )
    alterada = alterar_datas(db, reserva.id, cliente.id, AMANHA, AMANHA + timedelta(days=5), HOJE)
    assert alterada.valor_total_centimos == 25000


def test_cancelar_liberta_o_veiculo(db, veiculo, cliente, forma_pagamento):
    reserva = criar_reserva(
        db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=2), HOJE
    )
    cancelar_reserva(db, reserva.id, cliente.id)
    nova = criar_reserva(
        db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=2), HOJE
    )
    assert nova.id != reserva.id


def test_cliente_nao_ve_reserva_de_outro(db, veiculo, cliente, forma_pagamento):
    reserva = criar_reserva(
        db, cliente.id, veiculo.id, forma_pagamento.id, AMANHA, AMANHA + timedelta(days=2), HOJE
    )
    intruso = novo_cliente(db, "intruso@exemplo.pt")
    with pytest.raises(ErroReserva):
        obter_reserva_do_cliente(db, reserva.id, intruso.id)
    with pytest.raises(ErroReserva):
        cancelar_reserva(db, reserva.id, intruso.id)
