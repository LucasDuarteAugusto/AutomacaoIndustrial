from collections.abc import Sequence
from typing import Literal, Protocol

import httpx
import structlog

from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel

log = structlog.get_logger()

TipoEntradaEmbedding = Literal["document", "query"]


class ProvedorEmbedding(Protocol):
    """Contrato para gerar vetores usados na busca semântica."""

    @property
    def modelo(self) -> str: ...

    @property
    def dimensao(self) -> int: ...

    async def embed_documento(self, trechos: Sequence[str]) -> list[list[float]]:
        """Gera embeddings contextualizados dos trechos de um mesmo documento."""

    async def embed_consulta(self, consulta: str) -> list[float]:
        """Gera o vetor de uma pergunta de busca."""


class VoyageEmbedding:
    """Cliente HTTP do Voyage `voyage-context-4` (contextualized embeddings)."""

    def __init__(self, settings: Settings, cliente: httpx.AsyncClient) -> None:
        self._settings = settings
        self._cliente = cliente
        self._modelo = settings.embedding_modelo
        self._dimensao = settings.embedding_dimensao

    @property
    def modelo(self) -> str:
        return self._modelo

    @property
    def dimensao(self) -> int:
        return self._dimensao

    async def embed_documento(self, trechos: Sequence[str]) -> list[list[float]]:
        if not trechos:
            return []
        resposta = await self._chamar([[*trechos]], input_type="document")
        return resposta[0]

    async def embed_consulta(self, consulta: str) -> list[float]:
        texto = consulta.strip()
        if not texto:
            raise RegraNegocio("Consulta de embedding vazia")
        resposta = await self._chamar([[texto]], input_type="query")
        return resposta[0][0]

    async def _chamar(
        self,
        inputs: list[list[str]],
        *,
        input_type: TipoEntradaEmbedding,
    ) -> list[list[list[float]]]:
        chave = self._settings.voyage_api_key
        if chave is None:
            raise ServicoIndisponivel("VOYAGE_API_KEY não configurada")

        url = f"{self._settings.voyage_base_url.rstrip('/')}/contextualizedembeddings"
        corpo = {
            "inputs": inputs,
            "model": self._modelo,
            "input_type": input_type,
            "output_dimension": self._dimensao,
            "output_dtype": "float",
        }
        try:
            resposta = await self._cliente.post(
                url,
                headers={"Authorization": f"Bearer {chave.get_secret_value()}", "Content-Type": "application/json"},
                json=corpo,
                timeout=60.0,
            )
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            log.warning(
                "voyage_embedding_http_erro",
                status=erro.response.status_code,
                detalhe=erro.response.text[:500],
            )
            raise ServicoIndisponivel(f"Voyage embedding falhou ({erro.response.status_code})") from erro
        except httpx.HTTPError as erro:
            log.warning("voyage_embedding_rede_erro", erro=str(erro))
            raise ServicoIndisponivel("Voyage embedding indisponível") from erro

        dados = resposta.json()
        documentos: list[list[list[float]]] = []
        for documento in dados["data"]:
            trechos = [item["embedding"] for item in sorted(documento["data"], key=lambda item: item["index"])]
            if any(len(vetor) != self._dimensao for vetor in trechos):
                raise ServicoIndisponivel(
                    f"Voyage devolveu dimensão diferente de {self._dimensao} (modelo={self._modelo})"
                )
            documentos.append(trechos)
        return documentos


def criar_provedor_embedding(settings: Settings, cliente: httpx.AsyncClient) -> VoyageEmbedding:
    return VoyageEmbedding(settings, cliente)
