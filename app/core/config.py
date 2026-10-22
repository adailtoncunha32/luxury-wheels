import secrets
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# A raiz do projeto: este ficheiro está em app/core/, por isso subimos 2 níveis
RAIZ_PROJETO = Path(__file__).resolve().parents[2]

# parents[0] = core   parents[1] = app   parents[2] = luxury-wheels ✅
CAMINHO_BD = RAIZ_PROJETO / "luxury_wheels.db"


class Configuracoes(BaseSettings):
    database_url: str = "sqlite:///" + CAMINHO_BD.as_posix()
    secret_key: str = Field(default_factory=secrets.token_urlsafe)

    model_config = SettingsConfigDict(env_file=RAIZ_PROJETO / ".env", env_file_encoding="utf-8")


settings = Configuracoes()
