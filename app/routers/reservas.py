"""Reservas: criar (com resumo + pagamento simulado), listar, alterar datas e cancelar."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.models import Veiculo
from app.routers.deps import ClienteAutenticado, SessaoBD, adicionar_mensagem, renderizar
from app.services.reserva_service import (
    ErroReserva,
    alterar_datas,
    cancelar_reserva,
    criar_reserva,
    listar_formas_pagamento,
    listar_reservas_do_cliente,
    obter_reserva_do_cliente,
    preparar_resumo,
)

router = APIRouter(prefix="/reservas", tags=["reservas"])

# Campos de formulário reutilizados
DataForm = Annotated[date, Form()]
IdForm = Annotated[int, Form()]


def _pagina_nova_reserva(request, db, veiculo_id, contexto_extra=None, status_code=200):
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    contexto = {
        "veiculo": veiculo,
        "formas": listar_formas_pagamento(db),
        "hoje": date.today().isoformat(),
        **(contexto_extra or {}),
    }
    return renderizar(request, "reserva.html", contexto, status_code=status_code)


@router.get("/nova/{veiculo_id}")
def nova_reserva(
    request: Request,
    veiculo_id: int,
    db: SessaoBD,
    cliente: ClienteAutenticado,
    data_inicio: str | None = None,
    data_fim: str | None = None,
):
    hoje = date.today()
    sugestao = {
        "data_inicio": data_inicio or hoje.isoformat(),
        "data_fim": data_fim or (hoje + timedelta(days=1)).isoformat(),
    }
    return _pagina_nova_reserva(request, db, veiculo_id, sugestao)


@router.post("/resumo")
def resumo_reserva(
    request: Request,
    db: SessaoBD,
    cliente: ClienteAutenticado,
    veiculo_id: IdForm,
    forma_pagamento_id: IdForm,
    data_inicio: DataForm,
    data_fim: DataForm,
):
    """Passo 1 de 2: mostra o total e a forma de pagamento escolhida, ainda sem gravar."""
    datas = {"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()}
    try:
        resumo = preparar_resumo(db, veiculo_id, forma_pagamento_id, data_inicio, data_fim, date.today())
    except ErroReserva as erro:
        return _pagina_nova_reserva(request, db, veiculo_id, {"erro": str(erro), **datas}, status_code=400)
    return _pagina_nova_reserva(request, db, veiculo_id, {"resumo": resumo, **datas})


@router.post("")
def confirmar_reserva(
    request: Request,
    db: SessaoBD,
    cliente: ClienteAutenticado,
    veiculo_id: IdForm,
    forma_pagamento_id: IdForm,
    data_inicio: DataForm,
    data_fim: DataForm,
):
    """Passo 2 de 2: 'Pagar e concluir' (pagamento simulado) -> grava a reserva."""
    try:
        reserva = criar_reserva(
            db, cliente.id, veiculo_id, forma_pagamento_id, data_inicio, data_fim, date.today()
        )
    except ErroReserva as erro:
        datas = {"data_inicio": data_inicio.isoformat(), "data_fim": data_fim.isoformat()}
        return _pagina_nova_reserva(request, db, veiculo_id, {"erro": str(erro), **datas}, status_code=400)

    adicionar_mensagem(request, f"Pagamento aceite! Reserva n.º {reserva.id} confirmada.")
    return RedirectResponse("/reservas/minhas", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/minhas")
def minhas_reservas(request: Request, db: SessaoBD, cliente: ClienteAutenticado):
    reservas = listar_reservas_do_cliente(db, cliente.id)
    return renderizar(request, "minhas_reservas.html", {"reservas": reservas, "hoje": date.today()})


@router.get("/{reserva_id}/alterar")
def pagina_alterar(request: Request, reserva_id: int, db: SessaoBD, cliente: ClienteAutenticado):
    try:
        reserva = obter_reserva_do_cliente(db, reserva_id, cliente.id)
    except ErroReserva as erro:
        adicionar_mensagem(request, str(erro), "erro")
        return RedirectResponse("/reservas/minhas", status_code=status.HTTP_303_SEE_OTHER)
    return renderizar(request, "alterar_reserva.html", {"reserva": reserva, "hoje": date.today().isoformat()})


@router.post("/{reserva_id}/alterar")
def alterar(
    request: Request,
    reserva_id: int,
    db: SessaoBD,
    cliente: ClienteAutenticado,
    data_inicio: DataForm,
    data_fim: DataForm,
):
    try:
        reserva = alterar_datas(db, reserva_id, cliente.id, data_inicio, data_fim, date.today())
    except ErroReserva as erro:
        adicionar_mensagem(request, str(erro), "erro")
        return RedirectResponse(f"/reservas/{reserva_id}/alterar", status_code=status.HTTP_303_SEE_OTHER)

    adicionar_mensagem(request, f"Reserva n.º {reserva.id} alterada.")
    return RedirectResponse("/reservas/minhas", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{reserva_id}/cancelar")
def cancelar(request: Request, reserva_id: int, db: SessaoBD, cliente: ClienteAutenticado):
    try:
        cancelar_reserva(db, reserva_id, cliente.id)
        adicionar_mensagem(request, f"Reserva n.º {reserva_id} cancelada.")
    except ErroReserva as erro:
        adicionar_mensagem(request, str(erro), "erro")
    return RedirectResponse("/reservas/minhas", status_code=status.HTTP_303_SEE_OTHER)
