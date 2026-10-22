"""Ponto de entrada: monta a aplicação (middleware, ficheiros estáticos e routers)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.routers import auth, paginas, reservas, veiculos

PASTA_APP = Path(__file__).resolve().parent

app = FastAPI(title="Luxury Wheels")

# Cookie de sessão assinado com a SECRET_KEY (se alguém o alterar, a assinatura deixa de bater).
# same_site="lax": o browser não envia o cookie em POSTs vindos de outros sites (proteção CSRF).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    max_age=60 * 60 * 8,  # 8 horas
)

app.mount("/assets", StaticFiles(directory=PASTA_APP / "static"), name="assets")

app.include_router(paginas.router)
app.include_router(auth.router)
app.include_router(veiculos.router)
app.include_router(reservas.router)


@app.get("/health", tags=["sistema"])
def health():
    return {"status": "ok"}
