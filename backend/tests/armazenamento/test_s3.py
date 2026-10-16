from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from pydantic import SecretStr

from app.armazenamento.chave import chave_documento
from app.armazenamento.factory import criar_armazenamento
from app.armazenamento.s3 import ArmazenamentoS3
from app.core.config import Settings
from app.core.errors import ServicoIndisponivel


def _settings_s3(**extras: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://u:p@localhost:5433/db",
        "ambiente": "teste",
        "armazenamento_tipo": "s3",
        "s3_endpoint_url": "https://abc123.r2.cloudflarestorage.com",
        "s3_region": "auto",
        "s3_bucket": "automacao-industrial",
        "s3_access_key_id": SecretStr("ak"),
        "s3_secret_access_key": SecretStr("sk"),
    }
    base.update(extras)
    return Settings(**base)  # type: ignore[arg-type]


def _client_error(codigo: str) -> ClientError:
    return ClientError({"Error": {"Code": codigo, "Message": codigo}}, "HeadObject")


@pytest.mark.asyncio
async def test_s3_salvar_carregar_existe_apagar() -> None:
    corpo = MagicMock()
    corpo.read = AsyncMock(return_value=b"%PDF-1.4")
    cliente = AsyncMock()
    cliente.put_object = AsyncMock()
    cliente.get_object = AsyncMock(return_value={"Body": corpo})
    cliente.head_object = AsyncMock()
    cliente.delete_object = AsyncMock()

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=cliente)
    cm.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.client = MagicMock(return_value=cm)

    with patch("app.armazenamento.s3.aioboto3.Session", return_value=session):
        store = ArmazenamentoS3(_settings_s3())
        chave = chave_documento(uuid4(), "c" * 64)
        await store.salvar(chave, b"%PDF-1.4", content_type="application/pdf")
        assert await store.existe(chave) is True
        assert await store.carregar(chave) == b"%PDF-1.4"
        await store.apagar(chave)

    cliente.put_object.assert_awaited()
    cliente.delete_object.assert_awaited()
    assert session.client.call_args.kwargs["endpoint_url"] == "https://abc123.r2.cloudflarestorage.com"


@pytest.mark.asyncio
async def test_s3_existe_false_quando_404() -> None:
    cliente = AsyncMock()
    cliente.head_object = AsyncMock(side_effect=_client_error("404"))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=cliente)
    cm.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.client = MagicMock(return_value=cm)

    with patch("app.armazenamento.s3.aioboto3.Session", return_value=session):
        store = ArmazenamentoS3(_settings_s3())
        assert await store.existe("x/y.pdf") is False


def test_s3_sem_credenciais_falha_na_criacao() -> None:
    settings = _settings_s3(s3_access_key_id=None, s3_secret_access_key=None)
    with pytest.raises(ServicoIndisponivel, match="S3_BUCKET"):
        ArmazenamentoS3(settings)


def test_factory_cria_s3() -> None:
    store = criar_armazenamento(_settings_s3())
    assert isinstance(store, ArmazenamentoS3)


def test_factory_s3_sem_bucket_levanta() -> None:
    settings = _settings_s3(s3_bucket=None)
    with pytest.raises(ServicoIndisponivel):
        criar_armazenamento(settings)
