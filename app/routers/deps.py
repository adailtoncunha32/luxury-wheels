"""Peças partilhadas por todos os routers: templates, sessão da BD e o 'segurança à porta'."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import obter_sessao
from app.models import Cliente

PASTA_APP = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=PASTA_APP / "templates")


def formatar_euros(centimos: int) -> str:
    """6550 -> '65,50 €'  |  123456 -> '1 234,56 €'"""
    return f"{centimos / 100:,.2f} €".replace(",", " ").replace(".", ",")


def formatar_data(valor) -> str:
    return valor.strftime("%d/%m/%Y")


# Filtros Jinja: no HTML escreve-se {{ reserva.valor_total_centimos | euros }}
templates.env.filters["euros"] = formatar_euros
templates.env.filters["data_pt"] = formatar_data

# Atalho: em vez de "db: Session = Depends(obter_sessao)" em todas as rotas
SessaoBD = Annotated[Session, Depends(obter_sessao)]


def adicionar_mensagem(request: Request, texto: str, tipo: str = "sucesso") -> None:
    """Mensagem 'flash': guardada na sessão e mostrada UMA vez na próxima página."""
    mensagens = request.session.get("mensagens", [])
    mensagens.append({"texto": texto, "tipo": tipo})
    request.session["mensagens"] = mensagens


def renderizar(request: Request, template: str, contexto: dict | None = None, status_code: int = 200):
    contexto = {"mensagens": request.session.pop("mensagens", []), **(contexto or {})}
    return templates.TemplateResponse(request, template, contexto, status_code=status_code)


def iniciar_sessao(request: Request, cliente: Cliente) -> None:
    request.session.clear()  # começa uma sessão limpa (evita "session fixation")
    request.session["cliente_id"] = cliente.id
    request.session["cliente_nome"] = cliente.nome


def destino_seguro(proximo: str | None) -> str:
    """Só aceita caminhos internos ('/reservas/minhas'), nunca 'https://site-malicioso.com'."""
    if proximo and proximo.startswith("/") and not proximo.startswith("//") and "\\" not in proximo:
        return proximo
    return "/veiculos"


def obter_cliente_atual(request: Request, db: SessaoBD) -> Cliente | None:
    cliente_id = request.session.get("cliente_id")
    if cliente_id is None:
        return None
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:  # a conta já não existe: limpa o cookie
        request.session.clear()
    return cliente


ClienteOpcional = Annotated[Cliente | None, Depends(obter_cliente_atual)]


def exigir_cliente(request: Request, cliente: ClienteOpcional) -> Cliente:
    """O segurança à porta: sem sessão iniciada, manda para o login (e depois volta aqui)."""
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"/login?proximo={request.url.path}"},
        )
    return cliente


ClienteAutenticado = Annotated[Cliente, Depends(exigir_cliente)]
