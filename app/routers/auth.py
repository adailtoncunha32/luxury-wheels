"""Registo, login e logout (requisito 1)."""

from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse

from app.routers.deps import SessaoBD, adicionar_mensagem, destino_seguro, iniciar_sessao, renderizar
from app.services.auth_service import ErroAuth, autenticar, registar_cliente

router = APIRouter(tags=["autenticação"])


@router.get("/registo")
def pagina_registo(request: Request):
    return renderizar(request, "registo.html")


@router.post("/registo")
def registo(
    request: Request,
    db: SessaoBD,
    nome: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    telefone: Annotated[str | None, Form()] = None,
):
    try:
        cliente = registar_cliente(db, nome, email, password, telefone)
    except ErroAuth as erro:
        # Devolve o formulário preenchido (menos a password) com o erro
        dados = {"nome": nome, "email": email, "telefone": telefone}
        return renderizar(request, "registo.html", {"erro": str(erro), "dados": dados}, status_code=400)

    iniciar_sessao(request, cliente)
    adicionar_mensagem(request, f"Bem-vindo, {cliente.nome}! A tua conta foi criada.")
    return RedirectResponse("/veiculos", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def pagina_login(request: Request, proximo: str | None = None):
    return renderizar(request, "login.html", {"proximo": proximo})


@router.post("/login")
def login(
    request: Request,
    db: SessaoBD,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    proximo: Annotated[str | None, Form()] = None,
):
    cliente = autenticar(db, email, password)
    if cliente is None:
        contexto = {"erro": "Email ou password incorretos.", "email": email, "proximo": proximo}
        return renderizar(request, "login.html", contexto, status_code=401)

    iniciar_sessao(request, cliente)
    adicionar_mensagem(request, f"Olá de novo, {cliente.nome}!")
    return RedirectResponse(destino_seguro(proximo), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    adicionar_mensagem(request, "Sessão terminada. Até breve!")
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
