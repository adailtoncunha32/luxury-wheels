"""Páginas 'institucionais': início e contacto."""

from fastapi import APIRouter, Request

from app.models.enums import Categoria
from app.routers.deps import renderizar

router = APIRouter(tags=["páginas"])


@router.get("/")
def pagina_inicial(request: Request):
    return renderizar(request, "index.html", {"categorias": list(Categoria)})


@router.get("/contacto")
def contacto(request: Request):
    return renderizar(request, "contacto.html")
