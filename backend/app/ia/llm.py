from typing import Protocol

import httpx
import structlog

from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel

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
        try:
            resposta = await self._cliente.post(
                url,
                headers={"Authorization": f"Bearer {chave.get_secret_value()}", "Content-Type": "application/json"},
                json=corpo,
                timeout=120.0,
            )
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            log.warning(
                "openai_llm_http_erro",
                status=erro.response.status_code,
                detalhe=erro.response.text[:500],
            )
            raise ServicoIndisponivel(f"OpenAI LLM falhou ({erro.response.status_code})") from erro
        except httpx.HTTPError as erro:
            log.warning("openai_llm_rede_erro", erro=str(erro))
            raise ServicoIndisponivel("OpenAI LLM indisponível") from erro

        dados = resposta.json()
        try:
            conteudo = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            raise ServicoIndisponivel("Resposta do OpenAI sem conteúdo utilizável") from erro
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise ServicoIndisponivel("Resposta do OpenAI vazia")
        return conteudo


def criar_provedor_llm(settings: Settings, cliente: httpx.AsyncClient) -> OpenAILLM:
    return OpenAILLM(settings, cliente)
