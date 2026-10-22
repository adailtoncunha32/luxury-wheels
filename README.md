# Luxury Wheels 🚗

Website de aluguer de veículos: projeto final do curso de Python da Tokio School (Proposta A).
Feito com **FastAPI**, **SQLAlchemy 2.0** e **SQLite**, com templates **Jinja2**.

## Como correr (3 comandos)

Requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
uv sync                                        # instala as dependências
uv run python -m app.db.seed                   # cria a BD com veículos de demonstração
uv run fastapi dev app/main.py --port 8001     # arranca o servidor
```

Abre <http://127.0.0.1:8001>. A documentação automática da API está em <http://127.0.0.1:8001/docs>.

> Usamos a porta 8001 porque a 8000 estava ocupada por outro programa na máquina de desenvolvimento.
> Se a tua 8000 estiver livre, podes omitir o `--port`.

Para correr os testes: `uv run pytest -v`

## Funcionalidades (requisitos do enunciado)

| Requisito | Onde |
|---|---|
| Registo e autenticação | `routers/auth.py`, `services/auth_service.py` |
| Pesquisa por marca/modelo + filtros (categoria, transmissão, tipo, diária, pessoas) | `routers/veiculos.py`, `services/catalogo_service.py` |
| Reserva com data de início e fim | `routers/reservas.py`, `services/reserva_service.py` |
| Escolha da forma de pagamento e conclusão (simulada) | `POST /reservas/resumo` → `POST /reservas` |
| Alterar só as datas ou cancelar | `/reservas/{id}/alterar`, `/reservas/{id}/cancelar` |

## Critérios técnicos

- **BD SQL** com 4 tabelas: `veiculos`, `clientes`, `reservas`, `formas_pagamento` (`app/models/`).
- **Total = diária × dias**: `calcular_total()` em `services/reserva_service.py`.
- **Veículo reservado fica indisponível**: `ha_sobreposicao()` em `services/disponibilidade.py`.
- **Inspeção com mais de 1 ano ou revisão em atraso → indisponível**: `esta_operacional()`, no mesmo ficheiro.

## Arquitetura

```
browser → routers (HTTP) → services (regras de negócio) → models (SQLAlchemy) → SQLite
```

- **Dinheiro em cêntimos** (inteiros) para evitar erros de arredondamento de `float`.
- A reserva guarda o **valor total no momento da reserva**: se a diária mudar, o histórico não muda.
- Cancelar não apaga a linha: muda o `estado` para `cancelada` (*soft delete*).
- A regra das datas é defendida em dois sítios: no Python e com um `CHECK` na própria BD.

## Segurança

- Passwords guardadas com hash **Argon2** (`pwdlib`), nunca em texto.
- Sessão num cookie **assinado** com a `SECRET_KEY` (`SessionMiddleware`), com `SameSite=Lax` contra CSRF.
- Proteção **IDOR**: um cliente só consegue ver, alterar ou cancelar as suas próprias reservas.
- Queries parametrizadas pelo SQLAlchemy (sem SQL injection) e *autoescape* do Jinja2 (sem XSS).
- O redirecionamento depois do login só aceita caminhos internos (sem *open redirect*).
- `.env` e a BD `.db` estão no `.gitignore`.
