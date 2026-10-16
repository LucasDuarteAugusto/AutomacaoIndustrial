"""Rate limiting com backend em memória (Redis entra na etapa seguinte)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.errors import LimiteExcedido
from app.core.handlers import problema


class Limitador(Protocol):
    async def verificar(self, chave: str, limite: int, janela_segundos: int) -> tuple[bool, int]:
        """Retorna (permitido, retry_after_segundos)."""


class LimitadorMemoria:
    """Janela deslizante em processo (adequado a uma réplica)."""

    def __init__(self) -> None:
        self._eventos: dict[str, deque[float]] = defaultdict(deque)

    async def verificar(self, chave: str, limite: int, janela_segundos: int) -> tuple[bool, int]:
        agora = time.monotonic()
        inicio = agora - janela_segundos
        fila = self._eventos[chave]
        while fila and fila[0] < inicio:
            fila.popleft()
        if len(fila) >= limite:
            retry_after = max(1, int(janela_segundos - (agora - fila[0])) + 1)
            return False, retry_after
        fila.append(agora)
        return True, 0


@dataclass(frozen=True)
class RegraLimite:
    limite: int
    janela_segundos: int
    prefixo_chave: str


def _cliente_ip(request: Request) -> str:
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip() or "desconhecido"
    if request.client is not None:
        return request.client.host
    return "desconhecido"


def resolver_regra(path: str, settings: Settings) -> RegraLimite | None:
    if path in {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}:
        return None
    if path.startswith("/v1/auth/login") or path.startswith("/v1/auth/bootstrap"):
        return RegraLimite(
            settings.rate_limit_auth_por_minuto,
            60,
            "auth",
        )
    if path.startswith("/v1/agente"):
        return RegraLimite(settings.rate_limit_agente_por_minuto, 60, "agente")
    if path.startswith("/v1/busca"):
        return RegraLimite(settings.rate_limit_busca_por_minuto, 60, "busca")
    if path.startswith("/v1/"):
        return RegraLimite(settings.rate_limit_padrao_por_minuto, 60, "api")
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        settings: Settings,
        limitador: Limitador,
        chave_cliente: Callable[[Request], str] = _cliente_ip,
    ) -> None:
        super().__init__(app)
        self._settings = settings
        self._limitador = limitador
        self._chave_cliente = chave_cliente

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._settings.rate_limit_habilitado:
            return await call_next(request)

        regra = resolver_regra(request.url.path, self._settings)
        if regra is None:
            return await call_next(request)

        chave = f"{regra.prefixo_chave}:{self._chave_cliente(request)}"
        permitido, retry_after = await self._limitador.verificar(chave, regra.limite, regra.janela_segundos)
        if not permitido:
            erro = LimiteExcedido(
                (
                    f"Limite de {regra.limite} requisições por "
                    f"{regra.janela_segundos}s excedido. Tente novamente em breve."
                ),
                retry_after=retry_after,
            )
            resposta = problema(request, erro.status, erro.titulo, erro.detalhe)
            resposta.headers["Retry-After"] = str(erro.retry_after)
            return resposta

        return await call_next(request)


def criar_limitador(settings: Settings) -> Limitador:
    """Factory: memória agora; Redis na etapa de escala compartilhada."""
    _ = settings.rate_limit_backend  # reservado para redis
    return LimitadorMemoria()
