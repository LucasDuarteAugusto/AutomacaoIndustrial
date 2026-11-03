import asyncio
from typing import Protocol

import httpx
import structlog

from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel
from app.ia.retry import espera_para_retry

log = structlog.get_logger()


class ProvedorLLM(Protocol):
    """Contrato para geração de texto (agente e descrição de figuras)."""

    @property
    def modelo(self) -> str: ...

    async def completar(self, *, sistema: str, usuario: str) -> str:
        """Gera uma resposta a partir de instrução de sistema e mensagem do usuário."""


class OpenAILLM:
    """Cliente HTTP do OpenAI Chat Completions (padrão: GPT-5 mini)."""

    def __init__(self, settings: Settings, cliente: httpx.AsyncClient) -> None:
        self._settings = settings
        self._cliente = cliente
        self._modelo = settings.llm_modelo

    @property
    def modelo(self) -> str:
        return self._modelo

    async def completar(self, *, sistema: str, usuario: str) -> str:
        if not usuario.strip():
            raise RegraNegocio("Mensagem do usuário vazia para o LLM")

        chave = self._settings.openai_api_key
        if chave is None:
            raise ServicoIndisponivel("OPENAI_API_KEY não configurada")

        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
        corpo = {
            "model": self._modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
        }
        resposta = await self._post_com_retry(url, corpo, chave.get_secret_value())
        dados = resposta.json()
        try:
            conteudo = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            raise ServicoIndisponivel("Resposta do OpenAI sem conteúdo utilizável") from erro
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise ServicoIndisponivel("Resposta do OpenAI vazia")
        return conteudo

    async def _post_com_retry(self, url: str, corpo: dict[str, object], chave: str) -> httpx.Response:
        """Repete 429/5xx (ex.: 503 "high demand") com backoff exponencial."""
        max_tentativas = self._settings.llm_max_tentativas
        for tentativa in range(1, max_tentativas + 1):
            try:
                resposta = await self._cliente.post(
                    url,
                    headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
                    json=corpo,
                    timeout=120.0,
                )
                resposta.raise_for_status()
                return resposta
            except httpx.HTTPStatusError as erro:
                status = erro.response.status_code
                repetivel = status == 429 or status >= 500
                log.warning(
                    "openai_llm_http_erro",
                    status=status,
                    modelo=self._modelo,
                    base_url=self._settings.openai_base_url,
                    tentativa=tentativa,
                    max_tentativas=max_tentativas,
                    detalhe=erro.response.text[:500],
                )
                if not repetivel or tentativa >= max_tentativas:
                    raise ServicoIndisponivel(_mensagem_erro(status, self._modelo, tentativa, max_tentativas)) from erro
                espera = espera_para_retry(erro.response, tentativa, self._settings.llm_espera_base_segundos, teto=30.0)
                log.info("openai_llm_retry", status=status, tentativa=tentativa, espera_segundos=round(espera, 1))
                await asyncio.sleep(espera)
            except httpx.HTTPError as erro:
                log.warning("openai_llm_rede_erro", tentativa=tentativa, erro=str(erro))
                if tentativa >= max_tentativas:
                    raise ServicoIndisponivel("OpenAI LLM indisponível") from erro
                await asyncio.sleep(self._settings.llm_espera_base_segundos * 2 ** (tentativa - 1))
        raise ServicoIndisponivel("OpenAI LLM indisponível")  # pragma: no cover - laço sempre retorna ou levanta


def _mensagem_erro(status: int, modelo: str, tentativa: int, max_tentativas: int) -> str:
    if status == 404:
        return (
            f"Modelo '{modelo}' não encontrado no provedor. "
            "Ajuste LLM_MODELO para um modelo disponível na sua conta/provedor."
        )
    if status == 429:
        return f"OpenAI LLM recusou por rate limit (429) após {tentativa} de {max_tentativas} tentativas."
    if status >= 500:
        return (
            f"Provedor LLM sobrecarregado ou indisponível ({status}) após {tentativa} de {max_tentativas} tentativas. "
            "Tente novamente em instantes ou use outro LLM_MODELO."
        )
    return f"OpenAI LLM falhou ({status}) após {tentativa} de {max_tentativas} tentativas."


def criar_provedor_llm(settings: Settings, cliente: httpx.AsyncClient) -> OpenAILLM:
    return OpenAILLM(settings, cliente)
