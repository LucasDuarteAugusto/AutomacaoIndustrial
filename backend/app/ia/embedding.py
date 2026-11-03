import asyncio
import time
from collections.abc import Sequence
from typing import Literal, Protocol

import httpx
import structlog

from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel
from app.ia.retry import espera_para_retry

log = structlog.get_logger()

TipoEntradaEmbedding = Literal["document", "query"]


class _ContextoExcedido(Exception):
    """O conjunto de trechos não cabe na janela de contexto do modelo."""


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
        self._ultima_chamada = 0.0
        self._trava_intervalo = asyncio.Lock()

    @property
    def modelo(self) -> str:
        return self._modelo

    @property
    def dimensao(self) -> int:
        return self._dimensao

    async def embed_documento(self, trechos: Sequence[str]) -> list[list[float]]:
        if not trechos:
            return []
        try:
            resposta = await self._chamar([[*trechos]], input_type="document")
        except _ContextoExcedido:
            meio = len(trechos) // 2
            if meio == 0:
                raise ServicoIndisponivel(
                    "Um trecho sozinho excede a janela de contexto do Voyage (32K tokens). "
                    "Reduza INGESTAO_TAMANHO_TRECHO_CHARS."
                ) from None
            log.info("voyage_embedding_dividindo_lote", trechos=len(trechos), metade=meio)
            return await self.embed_documento(trechos[:meio]) + await self.embed_documento(trechos[meio:])
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
        resposta = await self._post_com_retry(url, corpo, chave.get_secret_value())
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

    async def _post_com_retry(self, url: str, corpo: dict[str, object], chave: str) -> httpx.Response:
        """Repete 429/5xx com backoff exponencial (respeita `Retry-After`)."""
        max_tentativas = self._settings.voyage_max_tentativas
        for tentativa in range(1, max_tentativas + 1):
            await self._aguardar_intervalo()
            try:
                resposta = await self._cliente.post(
                    url,
                    headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
                    json=corpo,
                    timeout=60.0,
                )
                resposta.raise_for_status()
                return resposta
            except httpx.HTTPStatusError as erro:
                status = erro.response.status_code
                if status == 400 and _contexto_excedido(erro.response):
                    log.warning("voyage_embedding_contexto_excedido", detalhe=erro.response.text[:500])
                    raise _ContextoExcedido from erro
                repetivel = status == 429 or status >= 500
                log.warning(
                    "voyage_embedding_http_erro",
                    status=status,
                    tentativa=tentativa,
                    max_tentativas=max_tentativas,
                    detalhe=erro.response.text[:500],
                )
                if not repetivel or tentativa >= max_tentativas:
                    raise ServicoIndisponivel(_mensagem_erro(status, tentativa, max_tentativas)) from erro
                espera = espera_para_retry(erro.response, tentativa, self._settings.voyage_espera_base_segundos)
                log.info("voyage_embedding_retry", status=status, tentativa=tentativa, espera_segundos=round(espera, 1))
                await asyncio.sleep(espera)
            except httpx.HTTPError as erro:
                log.warning("voyage_embedding_rede_erro", tentativa=tentativa, erro=str(erro))
                if tentativa >= max_tentativas:
                    raise ServicoIndisponivel("Voyage embedding indisponível") from erro
                espera = min(self._settings.voyage_espera_base_segundos * 2 ** (tentativa - 1), 120.0)
                await asyncio.sleep(espera)
        raise ServicoIndisponivel("Voyage embedding indisponível")  # pragma: no cover - laço sempre retorna ou levanta

    async def _aguardar_intervalo(self) -> None:
        """Mantém uma distância mínima entre chamadas (útil no tier grátis: 3 RPM)."""
        intervalo = self._settings.voyage_intervalo_minimo_segundos
        if intervalo <= 0:
            return
        async with self._trava_intervalo:
            decorrido = time.monotonic() - self._ultima_chamada
            if decorrido < intervalo:
                await asyncio.sleep(intervalo - decorrido)
            self._ultima_chamada = time.monotonic()


def _contexto_excedido(resposta: httpx.Response) -> bool:
    texto = resposta.text.lower()
    return "context window" in texto or "too many tokens" in texto


def _mensagem_erro(status: int, tentativa: int, max_tentativas: int) -> str:
    if status == 400:
        return (
            "Voyage embedding recusou o lote (400). Verifique o detalhe no log: "
            "se for janela de contexto, reduza INGESTAO_MAX_CHARS_LOTE_EMBEDDING."
        )
    if status == 429:
        return (
            f"Voyage embedding recusou por rate limit (429) após {tentativa} de {max_tentativas} tentativas. "
            "Confira o tier da conta (3 RPM / 10K TPM sem método de pagamento) e reduza "
            "INGESTAO_MAX_CHARS_LOTE_EMBEDDING (ex.: 30000) e/ou use VOYAGE_INTERVALO_MINIMO_SEGUNDOS=21."
        )
    return f"Voyage embedding falhou ({status}) após {tentativa} de {max_tentativas} tentativas."


def criar_provedor_embedding(settings: Settings, cliente: httpx.AsyncClient) -> VoyageEmbedding:
    return VoyageEmbedding(settings, cliente)
