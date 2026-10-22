"""Registo e autenticação de clientes (requisito 1)."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import gerar_hash, verificar_password
from app.models import Cliente

TAMANHO_MINIMO_PASSWORD = 8


class ErroAuth(Exception):
    """Erro de registo/login. A mensagem é mostrada ao utilizador."""


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def registar_cliente(
    db: Session, nome: str, email: str, password: str, telefone: str | None = None
) -> Cliente:
    nome = nome.strip()
    email = normalizar_email(email)
    telefone = (telefone or "").strip() or None

    if not nome:
        raise ErroAuth("Indica o teu nome.")
    if "@" not in email:
        raise ErroAuth("Indica um email válido.")
    if len(password) < TAMANHO_MINIMO_PASSWORD:
        raise ErroAuth(f"A password tem de ter pelo menos {TAMANHO_MINIMO_PASSWORD} caracteres.")
    if db.scalar(select(Cliente.id).where(Cliente.email == email)) is not None:
        raise ErroAuth("Já existe uma conta com esse email.")

    cliente = Cliente(nome=nome, email=email, password_hash=gerar_hash(password), telefone=telefone)
    db.add(cliente)
    try:
        db.commit()
    except IntegrityError:
        # Dois registos com o mesmo email ao mesmo tempo: a constraint UNIQUE da BD apanha-o.
        db.rollback()
        raise ErroAuth("Já existe uma conta com esse email.") from None
    db.refresh(cliente)
    return cliente


def autenticar(db: Session, email: str, password: str) -> Cliente | None:
    """Devolve o cliente se email+password estiverem certos; senão None (sem dizer qual falhou)."""
    cliente = db.scalar(select(Cliente).where(Cliente.email == normalizar_email(email)))
    if cliente is None or not verificar_password(password, cliente.password_hash):
        return None
    return cliente
