"""Testes 'de ponta a ponta': o browser de teste navega pelo site como um cliente real."""

from datetime import timedelta

from tests.conftest import HOJE


def test_pagina_inicial(client):
    assert client.get("/").status_code == 200


def test_catalogo_mostra_veiculo(client, veiculo):
    resposta = client.get("/veiculos")
    assert resposta.status_code == 200
    assert "Série 3" in resposta.text


def test_filtro_por_categoria_vazia_nao_rebenta(client, veiculo):
    resposta = client.get("/veiculos?categoria=&preco_max=&lugares=")
    assert resposta.status_code == 200


def test_filtro_exclui_outra_categoria(client, veiculo):
    resposta = client.get("/veiculos?categoria=Luxo")
    assert "Série 3" not in resposta.text


def test_area_privada_exige_login(client):
    resposta = client.get("/reservas/minhas", follow_redirects=False)
    assert resposta.status_code == 303
    assert resposta.headers["location"].startswith("/login")


def test_fluxo_completo_registo_reserva_cancelamento(client, veiculo, forma_pagamento):
    # 1. Registo (fica logo com sessão iniciada)
    resposta = client.post(
        "/registo", data={"nome": "Ana", "email": "ana@exemplo.pt", "password": "password-segura"}
    )
    assert resposta.status_code == 200

    # 2. Reservar: resumo com o total e depois "Pagar e concluir"
    inicio = (HOJE + timedelta(days=1)).isoformat()
    fim = (HOJE + timedelta(days=4)).isoformat()
    dados = {
        "veiculo_id": veiculo.id,
        "forma_pagamento_id": forma_pagamento.id,
        "data_inicio": inicio,
        "data_fim": fim,
    }
    resumo = client.post("/reservas/resumo", data=dados)
    assert "150,00 €" in resumo.text  # 3 dias x 50 €

    final = client.post("/reservas", data=dados)
    assert "confirmada" in final.text

    # 3. Cancelar
    cancelada = client.post("/reservas/1/cancelar")
    assert "cancelada" in cancelada.text


def test_login_errado_devolve_401(client):
    resposta = client.post("/login", data={"email": "ninguem@exemplo.pt", "password": "errada123"})
    assert resposta.status_code == 401
