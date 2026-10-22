"""Catálogo e pesquisa de veículos (requisito 2)."""

from datetime import date, timedelta

from fastapi import APIRouter, Request

from app.models.enums import Categoria, TipoVeiculo, Transmissao
from app.routers.deps import SessaoBD, renderizar
from app.services.catalogo_service import FAIXAS_LUGARES, FiltrosPesquisa, pesquisar_veiculos

router = APIRouter(prefix="/veiculos", tags=["veículos"])


# Um <form method="get"> envia os campos vazios como "" (ex.: ?categoria=).
# Por isso recebemos tudo como texto e convertemos aqui, com calma.
def _ler_enum(classe, valor: str | None):
    try:
        return classe(valor) if valor else None
    except ValueError:
        return None


def _ler_data(valor: str | None) -> date | None:
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def _ler_preco_centimos(valor: str | None) -> int | None:
    try:
        return round(float(valor.replace(",", ".")) * 100) if valor else None
    except ValueError:
        return None


@router.get("")
def listar_veiculos(
    request: Request,
    db: SessaoBD,
    q: str | None = None,
    categoria: str | None = None,
    transmissao: str | None = None,
    tipo: str | None = None,
    preco_max: str | None = None,
    lugares: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
):
    hoje = date.today()
    inicio = _ler_data(data_inicio) or hoje
    fim = _ler_data(data_fim) or inicio + timedelta(days=1)
    erro = None
    if fim <= inicio:
        erro = "A data de devolução tem de ser depois da data de levantamento."
        fim = inicio + timedelta(days=1)

    filtros = FiltrosPesquisa(
        inicio=inicio,
        fim=fim,
        texto=(q or "").strip() or None,
        categoria=_ler_enum(Categoria, categoria),
        transmissao=_ler_enum(Transmissao, transmissao),
        tipo=_ler_enum(TipoVeiculo, tipo),
        preco_max_centimos=_ler_preco_centimos(preco_max),
        lugares=lugares,
    )

    contexto = {
        "veiculos": pesquisar_veiculos(db, filtros, hoje),
        "filtros": filtros,
        "valores": request.query_params,
        "categorias": list(Categoria),
        "transmissoes": list(Transmissao),
        "tipos": list(TipoVeiculo),
        "faixas_lugares": list(FAIXAS_LUGARES),
        "hoje": hoje,
        "erro": erro,
    }
    return renderizar(request, "veiculos.html", contexto)
