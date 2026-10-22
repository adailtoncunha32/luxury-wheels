from enum import StrEnum


class Categoria(StrEnum):
    PEQUENO = "Pequeno"
    MEDIO = "Médio"
    GRANDE = "Grande"
    SUV = "SUV"
    LUXO = "Luxo"


class Transmissao(StrEnum):
    AUTOMATICO = "Automático"
    MANUAL = "Manual"


class TipoVeiculo(StrEnum):
    CARRO = "Carro"
    MOTO = "Moto"


class EstadoReserva(StrEnum):
    ATIVA = "ativa"
    CANCELADA = "cancelada"
