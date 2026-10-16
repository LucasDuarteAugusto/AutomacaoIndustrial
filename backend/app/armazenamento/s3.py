from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aioboto3
import structlog
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.core.errors import ServicoIndisponivel

log = structlog.get_logger()


class ArmazenamentoS3:
    """Object storage S3-compatível: Cloudflare R2 agora, AWS S3 depois (mesmo cliente)."""

    def __init__(self, settings: Settings) -> None:
        if not settings.s3_bucket or not settings.s3_access_key_id or not settings.s3_secret_access_key:
            raise ServicoIndisponivel("Armazenamento S3/R2 exige S3_BUCKET, S3_ACCESS_KEY_ID e S3_SECRET_ACCESS_KEY")
        self._bucket = settings.s3_bucket
        self._endpoint_url = settings.s3_endpoint_url
        self._region = settings.s3_region
        self._access_key = settings.s3_access_key_id.get_secret_value()
        self._secret_key = settings.s3_secret_access_key.get_secret_value()
        self._session = aioboto3.Session()

    @asynccontextmanager
    async def _cliente(self) -> AsyncIterator[Any]:
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        ) as cliente:
            yield cliente

    async def salvar(self, chave: str, conteudo: bytes, *, content_type: str = "application/octet-stream") -> None:
        try:
            async with self._cliente() as s3:
                await s3.put_object(
                    Bucket=self._bucket,
                    Key=chave,
                    Body=conteudo,
                    ContentType=content_type,
                )
        except ClientError as erro:
            log.warning("armazenamento_s3_salvar_erro", chave=chave, erro=str(erro))
            raise ServicoIndisponivel(f"Falha ao gravar objeto S3/R2: {chave}") from erro
        log.info("armazenamento_s3_salvo", chave=chave, bytes=len(conteudo), bucket=self._bucket)

    async def carregar(self, chave: str) -> bytes:
        try:
            async with self._cliente() as s3:
                resposta = await s3.get_object(Bucket=self._bucket, Key=chave)
                corpo = await resposta["Body"].read()
        except ClientError as erro:
            codigo = erro.response.get("Error", {}).get("Code", "")
            if codigo in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(chave) from erro
            log.warning("armazenamento_s3_carregar_erro", chave=chave, erro=str(erro))
            raise ServicoIndisponivel(f"Falha ao ler objeto S3/R2: {chave}") from erro
        return bytes(corpo)

    async def existe(self, chave: str) -> bool:
        try:
            async with self._cliente() as s3:
                await s3.head_object(Bucket=self._bucket, Key=chave)
        except ClientError as erro:
            codigo = erro.response.get("Error", {}).get("Code", "")
            if codigo in {"404", "NoSuchKey", "NotFound"}:
                return False
            log.warning("armazenamento_s3_existe_erro", chave=chave, erro=str(erro))
            raise ServicoIndisponivel(f"Falha ao verificar objeto S3/R2: {chave}") from erro
        return True

    async def apagar(self, chave: str) -> None:
        try:
            async with self._cliente() as s3:
                await s3.delete_object(Bucket=self._bucket, Key=chave)
        except ClientError as erro:
            log.warning("armazenamento_s3_apagar_erro", chave=chave, erro=str(erro))
            raise ServicoIndisponivel(f"Falha ao apagar objeto S3/R2: {chave}") from erro
        log.info("armazenamento_s3_apagado", chave=chave, bucket=self._bucket)
