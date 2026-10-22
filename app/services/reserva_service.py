"""O balcão de contratos: criar, alterar e cancelar reservas.

Os routers chamam estas funções; aqui ficam TODAS as regras de negócio das reservas.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FormaPagamento, Reserva, Veiculo
from app.models.enums import EstadoReserva
from app.services.disponibilidade import esta_operacional, ha_sobreposicao


class ErroReserva(Exception):
    """Erro de regra de negócio. A mensagem é mostrada tal e qual ao cliente."""


def calcular_dias(inicio: date, fim: date) -> int:
    return (fim - inicio).days


def calcular_total(valor_diaria_centimos: int, inicio: date, fim: date) -> int:
    """Critério 3: total = valor da diária x número de dias (em cêntimos)."""
    dias = calcular_dias(inicio, fim)
    if dias < 1:
        raise ErroReserva("A data de fim tem de ser posterior à data de início.")
    return valor_diaria_centimos * dias


def validar_datas(inicio: date, fim: date, hoje: date) -> None:
    if inicio < hoje:
        raise ErroReserva("A data de início não pode ser no passado.")
    if fim <= inicio:
        raise ErroReserva("A data de fim tem de ser posterior à data de início.")


def listar_formas_pagamento(db: Session) -> list[FormaPagamento]:
    consulta = select(FormaPagamento).where(FormaPagamento.ativa.is_(True)).order_by(FormaPagamento.nome)
    return list(db.scalars(consulta))


def _obter_veiculo_reservavel(db: Session, veiculo_id: int, hoje: date) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None or not esta_operacional(veiculo, hoje):
        raise ErroReserva("Este veículo não está disponível para reserva.")
    return veiculo


def _obter_forma_pagamento(db: Session, forma_pagamento_id: int) -> FormaPagamento:
    forma = db.get(FormaPagamento, forma_pagamento_id)
    if forma is None or not forma.ativa:
        raise ErroReserva("Escolhe uma forma de pagamento válida.")
    return forma


def preparar_resumo(
    db: Session, veiculo_id: int, forma_pagamento_id: int, inicio: date, fim: date, hoje: date
) -> dict:
    """Valida tudo e calcula o total SEM gravar nada (é o ecrã antes de 'Pagar')."""
    validar_datas(inicio, fim, hoje)
    veiculo = _obter_veiculo_reservavel(db, veiculo_id, hoje)
    forma = _obter_forma_pagamento(db, forma_pagamento_id)
    if ha_sobreposicao(db, veiculo.id, inicio, fim):
        raise ErroReserva("O veículo já está reservado nessas datas. Experimenta outras datas.")
    return {
        "veiculo": veiculo,
        "forma": forma,
        "inicio": inicio,
        "fim": fim,
        "dias": calcular_dias(inicio, fim),
        "total_centimos": calcular_total(veiculo.valor_diaria_centimos, inicio, fim),
    }


def criar_reserva(
    db: Session,
    cliente_id: int,
    veiculo_id: int,
    forma_pagamento_id: int,
    inicio: date,
    fim: date,
    hoje: date,
) -> Reserva:
    """Volta a validar tudo (nunca confiar no que veio do browser) e grava a reserva."""
    resumo = preparar_resumo(db, veiculo_id, forma_pagamento_id, inicio, fim, hoje)
    reserva = Reserva(
        cliente_id=cliente_id,
        veiculo_id=veiculo_id,
        forma_pagamento_id=forma_pagamento_id,
        data_inicio=inicio,
        data_fim=fim,
        valor_total_centimos=resumo["total_centimos"],
    )
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


def listar_reservas_do_cliente(db: Session, cliente_id: int) -> list[Reserva]:
    consulta = select(Reserva).where(Reserva.cliente_id == cliente_id).order_by(Reserva.data_inicio.desc())
    return list(db.scalars(consulta))


def obter_reserva_do_cliente(db: Session, reserva_id: int, cliente_id: int) -> Reserva:
    """Proteção anti-IDOR: só devolve a reserva se pertencer a este cliente."""
    reserva = db.get(Reserva, reserva_id)
    if reserva is None or reserva.cliente_id != cliente_id:
        # Mesma mensagem nos dois casos: não revelamos se a reserva existe.
        raise ErroReserva("Reserva não encontrada.")
    return reserva


def alterar_datas(
    db: Session, reserva_id: int, cliente_id: int, novo_inicio: date, novo_fim: date, hoje: date
) -> Reserva:
    """Requisito 5: altera SÓ as datas e recalcula o total."""
    reserva = obter_reserva_do_cliente(db, reserva_id, cliente_id)
    if reserva.estado == EstadoReserva.CANCELADA:
        raise ErroReserva("Esta reserva está cancelada e já não pode ser alterada.")
    validar_datas(novo_inicio, novo_fim, hoje)
    if ha_sobreposicao(db, reserva.veiculo_id, novo_inicio, novo_fim, ignorar_reserva_id=reserva.id):
        raise ErroReserva("O veículo já está reservado nessas datas. Experimenta outras datas.")
    reserva.data_inicio = novo_inicio
    reserva.data_fim = novo_fim
    reserva.valor_total_centimos = calcular_total(
        reserva.veiculo.valor_diaria_centimos, novo_inicio, novo_fim
    )
    db.commit()
    return reserva


def cancelar_reserva(db: Session, reserva_id: int, cliente_id: int) -> Reserva:
    """Requisito 5: cancelamento total. Soft delete: a linha fica, muda o estado."""
    reserva = obter_reserva_do_cliente(db, reserva_id, cliente_id)
    if reserva.estado == EstadoReserva.CANCELADA:
        raise ErroReserva("Esta reserva já estava cancelada.")
    reserva.estado = EstadoReserva.CANCELADA
    db.commit()
    return reserva
