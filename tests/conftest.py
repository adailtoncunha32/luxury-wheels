"""Fixtures partilhadas: uma BD SQLite EM MEMÓRIA, nova e vazia para cada teste."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import gerar_hash
from app.db.base import Base
from app.db.session import obter_sessao
from app.main import app
from app.models import Cliente, FormaPagamento, Veiculo
from app.models.enums import Categoria, TipoVeiculo, Transmissao

HOJE = date.today()


@pytest.fixture
def db():
    # StaticPool + "sqlite://" = uma única ligação a uma BD que só existe em memória
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _ativar_fk(ligacao, _registo):
        ligacao.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False)
    with Sessao() as sessao:
        yield sessao
    engine.dispose()


def novo_veiculo(db, **alteracoes) -> Veiculo:
    dados = {
        "marca": "BMW",
        "modelo": "Série 3",
        "categoria": Categoria.MEDIO,
        "transmissao": Transmissao.AUTOMATICO,
        "tipo": TipoVeiculo.CARRO,
        "lugares": 5,
        "imagem": "/assets/images/cars/s3.jpg",
        "valor_diaria_centimos": 5000,
        "data_ultima_revisao": HOJE - timedelta(days=30),
        "data_proxima_revisao": HOJE + timedelta(days=150),
        "data_ultima_inspecao": HOJE - timedelta(days=100),
    }
    dados.update(alteracoes)
    veiculo = Veiculo(**dados)
    db.add(veiculo)
    db.commit()
    return veiculo


@pytest.fixture
def veiculo(db) -> Veiculo:
    return novo_veiculo(db)


@pytest.fixture
def forma_pagamento(db) -> FormaPagamento:
    forma = FormaPagamento(nome="MB Way")
    db.add(forma)
    db.commit()
    return forma


def novo_cliente(db, email="ana@exemplo.pt") -> Cliente:
    cliente = Cliente(nome="Ana", email=email, password_hash=gerar_hash("password-segura"))
    db.add(cliente)
    db.commit()
    return cliente


@pytest.fixture
def cliente(db) -> Cliente:
    return novo_cliente(db)


@pytest.fixture
def client(db):
    """Browser de teste: as rotas usam a BD em memória em vez do ficheiro .db."""
    app.dependency_overrides[obter_sessao] = lambda: db
    with TestClient(app) as browser:
        yield browser
    app.dependency_overrides.clear()
