"""Rate limiting com backend em memória ou Redis (compartilhado entre réplicas)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.errors import LimiteExcedido, RegraNegocio
from app.core.handlers import problema


class Limitador(Protocol):
    async def verificar(self, chave: str, limite: int, janela_segundos: int) -> tuple[bool, int]:
        """Retorna (permitido, retry_after_segundos)."""

    async def fechar(self) -> None: ...


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

    async def fechar(self) -> None:
        return None


class LimitadorRedis:
    """Janela deslizante compartilhada via Redis (várias réplicas da API)."""

    def __init__(self, cliente: Redis) -> None:
        self._cliente = cliente

    async def verificar(self, chave: str, limite: int, janela_segundos: int) -> tuple[bool, int]:
        agora = time.time()
        inicio = agora - janela_segundos
        chave_r = f"rl:{chave}"
        await self._cliente.zremrangebyscore(chave_r, 0, inicio)
        total = int(await self._cliente.zcard(chave_r))
        if total >= limite:
            mais_antigo = await self._cliente.zrange(chave_r, 0, 0, withscores=True)
            if mais_antigo:
                score = float(mais_antigo[0][1])
                retry_after = max(1, int(janela_segundos - (agora - score)) + 1)
            else:
                retry_after = janela_segundos
            return False, retry_after
        membro = f"{agora:.6f}"
        await self._cliente.zadd(chave_r, {membro: agora})
        await self._cliente.expire(chave_r, janela_segundos)
        return True, 0

    async def fechar(self) -> None:
        await self._cliente.aclose()


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
    if path.startswith(("/v1/auth/login", "/v1/auth/bootstrap", "/v1/auth/me/senha")):
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
    if settings.rate_limit_backend == "redis":
        if not settings.redis_url:
            raise RegraNegocio("RATE_LIMIT_BACKEND=redis exige REDIS_URL.")
        cliente = Redis.from_url(settings.redis_url, decode_responses=True)
        return LimitadorRedis(cliente)
    return LimitadorMemoria()
