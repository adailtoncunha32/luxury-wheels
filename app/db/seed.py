"""Cria as tabelas e enche a BD com veículos e formas de pagamento de demonstração.

Correr com:  uv run python -m app.db.seed
"""

from datetime import date, timedelta

from sqlalchemy import func, select

import app.models  # noqa: F401  (regista as 4 tabelas no Base.metadata)
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import FormaPagamento, Veiculo
from app.models.enums import Categoria, TipoVeiculo, Transmissao

FORMAS_PAGAMENTO = ["Cartão de Crédito", "MB Way", "PayPal"]


def dias(n: int) -> date:
    """Datas relativas a hoje: a demonstração continua válida em qualquer dia."""
    return date.today() + timedelta(days=n)


def _veiculo(marca, modelo, categoria, transmissao, tipo, lugares, imagem, diaria_euros, **datas):
    revisao_ok = {
        "data_ultima_revisao": dias(-60),
        "data_proxima_revisao": dias(120),
        "data_ultima_inspecao": dias(-100),
    }
    revisao_ok.update(datas)
    return Veiculo(
        marca=marca,
        modelo=modelo,
        categoria=categoria,
        transmissao=transmissao,
        tipo=tipo,
        lugares=lugares,
        imagem=f"/assets/images/cars/{imagem}",
        valor_diaria_centimos=round(diaria_euros * 100),
        **revisao_ok,
    )


def criar_veiculos() -> list[Veiculo]:
    C, M = TipoVeiculo.CARRO, TipoVeiculo.MOTO
    A, MAN = Transmissao.AUTOMATICO, Transmissao.MANUAL
    return [
        _veiculo("Mitsubishi", "Space Star", Categoria.PEQUENO, MAN, C, 4, "5.jpg", 29.90),
        _veiculo("Mitsubishi", "Mirage", Categoria.PEQUENO, A, C, 4, "b1.jpg", 32.50),
        _veiculo("Subaru", "Legacy", Categoria.MEDIO, A, C, 5, "3.jpg", 49.00),
        _veiculo("BMW", "Série 3", Categoria.MEDIO, A, C, 5, "s3.jpg", 65.00),
        _veiculo("Volkswagen", "Golf Sportsvan", Categoria.MEDIO, MAN, C, 5, "6.jpg", 45.00),
        _veiculo("Toyota", "Tacoma", Categoria.GRANDE, A, C, 5, "8.jpg", 85.00),
        _veiculo("Mitsubishi", "Pajero", Categoria.GRANDE, MAN, C, 7, "4.jpg", 79.00),
        _veiculo("Nissan", "Qashqai", Categoria.SUV, MAN, C, 5, "s2.jpg", 59.00),
        _veiculo("Mitsubishi", "Pajero Sport", Categoria.SUV, A, C, 7, "1.jpg", 75.00),
        _veiculo("Audi", "Q8", Categoria.LUXO, A, C, 5, "s4.jpg", 180.00),
        _veiculo("Porsche", "911 Speedster", Categoria.LUXO, MAN, C, 2, "9.jpg", 290.00),
        _veiculo("Rolls-Royce", "Ghost", Categoria.LUXO, A, C, 4, "7.jpg", 450.00),
        _veiculo("Yamaha", "MT-07", Categoria.PEQUENO, MAN, M, 2, "moto.jpg", 39.00),
        # Estes dois existem para DEMONSTRAR o critério 5 (não aparecem no catálogo):
        _veiculo(
            "Subaru", "Forester", Categoria.SUV, A, C, 5, "2.jpg", 55.00, data_ultima_inspecao=dias(-400)
        ),  # inspeção com mais de 1 ano
        _veiculo(
            "Mitsubishi",
            "Lancer Evolution",
            Categoria.MEDIO,
            MAN,
            C,
            5,
            "v2.jpg",
            69.00,
            data_proxima_revisao=dias(-5),
        ),  # revisão em atraso
    ]


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if (db.scalar(select(func.count()).select_from(Veiculo)) or 0) > 0:
            print("A base de dados já tem dados. Nada a fazer.")
            return
        db.add_all(criar_veiculos())
        db.add_all([FormaPagamento(nome=nome) for nome in FORMAS_PAGAMENTO])
        db.commit()
        print("Base de dados criada com veículos e formas de pagamento.")


if __name__ == "__main__":
    main()
