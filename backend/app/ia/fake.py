from collections.abc import Sequence

from app.core.errors import RegraNegocio
from app.core.ia_defaults import EMBEDDING_DIMENSAO_PADRAO


class EmbeddingFake:
    """Embedding determinístico para testes (sem chamar Voyage)."""

    def __init__(self, dimensao: int = EMBEDDING_DIMENSAO_PADRAO) -> None:
        self._dimensao = dimensao

    @property
    def modelo(self) -> str:
        return "fake-embedding"

    @property
    def dimensao(self) -> int:
        return self._dimensao

    async def embed_documento(self, trechos: Sequence[str]) -> list[list[float]]:
        return [self._vetor(texto) for texto in trechos]

    async def embed_consulta(self, consulta: str) -> list[float]:
        texto = consulta.strip()
        if not texto:
            raise RegraNegocio("Consulta de embedding vazia")
        return self._vetor(texto)

    def _vetor(self, texto: str) -> list[float]:
        vetor = [0.0] * self._dimensao
        if not texto:
            return vetor
        vetor[0] = (len(texto) % 1000) / 1000.0
        vetor[1] = (sum(ord(c) for c in texto[:64]) % 1000) / 1000.0
        return vetor
