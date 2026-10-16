from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.ia_defaults import (
    EMBEDDING_DIMENSAO_PADRAO,
    EMBEDDING_MODELO_PADRAO,
    LLM_MODELO_PADRAO,
    OPENAI_BASE_URL_PADRAO,
    VOYAGE_BASE_URL_PADRAO,
)

_CAMPOS_VAZIOS_COMO_NONE = frozenset(
    {
        "voyage_api_key",
        "openai_api_key",
        "s3_endpoint_url",
        "s3_bucket",
        "s3_access_key_id",
        "s3_secret_access_key",
    }
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

    # local = pasta no disco; s3 = API S3-compatível (Cloudflare R2 ou AWS S3)
    armazenamento_tipo: Literal["local", "s3"] = "local"
    armazenamento_caminho: str = "data/arquivos"
    armazenamento_tamanho_max_bytes: int = Field(default=50 * 1024 * 1024, ge=1024)
    ingestao_tamanho_trecho_chars: int = Field(default=2500, ge=200, le=20000)
    ingestao_max_chars_lote_embedding: int = Field(default=80_000, ge=1000)
    busca_candidatos_por_modo: int = Field(default=40, ge=5, le=200)
    busca_rrf_k: int = Field(default=60, ge=1, le=200)
    s3_endpoint_url: str | None = None  # R2: https://<accountid>.r2.cloudflarestorage.com; AWS: omitir
    s3_region: str = "auto"
    s3_bucket: str | None = None
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None

    jwt_secret: SecretStr = SecretStr("altere-este-segredo-em-producao-32b")
    jwt_algorithm: str = "HS256"
    jwt_expiracao_minutos: int = Field(default=480, ge=5, le=60 * 24 * 30)
    # Lista separada por vírgula; use * para refletir qualquer origem (só em local)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_lista(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

    @field_validator(*sorted(_CAMPOS_VAZIOS_COMO_NONE), mode="before")
    @classmethod
    def _vazio_vira_none(cls, valor: object) -> object:
        if valor == "":
            return None
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()
