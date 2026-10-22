from enum import StrEnum


class Categoria(StrEnum):
    PEQUENO = "pequeno"
    MEDIO = "medio"
    GRANDE = "grande"
    SUV = "SUV"
    LUXO = "luxo"


class Trasmissao(StrEnum):
    AUTOMATICO = "automatico"
    MANUAL = "manual"


class TipoVeiculo(StrEnum):
    CARRO = "carro"
    MOTO = "moto"


class EstadoReserva(StrEnum):
    ATIVA = "ativa"
    CANCELADA = "cancelada"

    
    