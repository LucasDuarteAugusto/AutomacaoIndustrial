from typing import Protocol


class ArmazenamentoArquivos(Protocol):
    """Contrato para persistir PDFs e outros binários fora do banco."""

    async def salvar(self, chave: str, conteudo: bytes, *, content_type: str = "application/octet-stream") -> None:
        """Grava ou sobrescreve o objeto identificado por `chave`."""

    async def carregar(self, chave: str) -> bytes:
        """Lê o conteúdo completo do objeto. Levanta FileNotFoundError se não existir."""

    async def existe(self, chave: str) -> bool:
        """Indica se a chave está presente no armazenamento."""

    async def apagar(self, chave: str) -> None:
        """Remove a chave se existir; no-op se já não houver objeto."""
