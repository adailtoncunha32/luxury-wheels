from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PASTA_APP = Path(__file__).resolve().parent

app = FastAPI(title="Luxury Wheels")

app.mount("/assets", StaticFiles(directory=PASTA_APP / "static"), name="assets")
templates = Jinja2Templates(directory=PASTA_APP / "templates")


@app.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}