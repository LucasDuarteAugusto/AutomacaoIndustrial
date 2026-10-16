import asyncio
from pathlib import Path

import structlog

from app.core.errors import RegraNegocio

log = structlog.get_logger()


class ArmazenamentoLocal:
    """Persistência em pasta do disco. Adequado a desenvolvimento e testes."""

    def __init__(self, raiz: Path) -> None:
        self._raiz = raiz.resolve()

    @property
    def raiz(self) -> Path:
        return self._raiz

    def _caminho(self, chave: str) -> Path:
        if not chave or chave.startswith("/") or "\\" in chave or ".." in Path(chave).parts:
            raise RegraNegocio(f"Chave de arquivo inválida: {chave!r}")
        destino = (self._raiz / chave).resolve()
        try:
            destino.relative_to(self._raiz)
        except ValueError as erro:
            raise RegraNegocio(f"Chave de arquivo fora da raiz: {chave!r}") from erro
        return destino

    async def salvar(self, chave: str, conteudo: bytes, *, content_type: str = "application/octet-stream") -> None:
        del content_type  # metadado só faz sentido em object storage
        caminho = self._caminho(chave)

        def _gravar() -> None:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_bytes(conteudo)

        await asyncio.to_thread(_gravar)
        log.info("armazenamento_local_salvo", chave=chave, bytes=len(conteudo))

    async def carregar(self, chave: str) -> bytes:
        caminho = self._caminho(chave)

        def _ler() -> bytes:
            if not caminho.is_file():
                raise FileNotFoundError(chave)
            return caminho.read_bytes()

        return await asyncio.to_thread(_ler)

    async def existe(self, chave: str) -> bool:
        caminho = self._caminho(chave)
        return await asyncio.to_thread(caminho.is_file)

    async def apagar(self, chave: str) -> None:
        caminho = self._caminho(chave)

        def _remover() -> None:
            if caminho.is_file():
                caminho.unlink()
            pai = caminho.parent
            if pai != self._raiz and pai.is_dir() and not any(pai.iterdir()):
                pai.rmdir()

        await asyncio.to_thread(_remover)
        log.info("armazenamento_local_apagado", chave=chave)
