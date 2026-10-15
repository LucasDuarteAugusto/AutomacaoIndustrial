from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.ia_defaults import (
    EMBEDDING_DIMENSAO_PADRAO,
    EMBEDDING_MODELO_PADRAO,
    LLM_MODELO_PADRAO,
    OPENAI_BASE_URL_PADRAO,
    VOYAGE_BASE_URL_PADRAO,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    nome_app: str = "AutomacaoIndustrial"
    ambiente: Literal["local", "teste", "producao"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False

    database_url: PostgresDsn
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    voyage_api_key: SecretStr | None = None
    voyage_base_url: str = VOYAGE_BASE_URL_PADRAO
    embedding_modelo: str = EMBEDDING_MODELO_PADRAO
    embedding_dimensao: int = Field(default=EMBEDDING_DIMENSAO_PADRAO, ge=256, le=2000)

    openai_api_key: SecretStr | None = None
    openai_base_url: str = OPENAI_BASE_URL_PADRAO
    llm_modelo: str = LLM_MODELO_PADRAO


@lru_cache
def get_settings() -> Settings:
    return Settings()
