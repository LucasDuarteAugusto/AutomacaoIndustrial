from unittest.mock import AsyncMock

from app.core.rate_limit import LimitadorRedis


async def test_limitador_redis_permite_ate_o_limite() -> None:
    cliente = AsyncMock()
    cliente.zremrangebyscore = AsyncMock(return_value=0)
    cliente.zcard = AsyncMock(side_effect=[0, 1, 2])
    cliente.zadd = AsyncMock(return_value=1)
    cliente.expire = AsyncMock(return_value=True)

    limitador = LimitadorRedis(cliente)
    assert (await limitador.verificar("auth:1.1.1.1", 2, 60)) == (True, 0)
    assert (await limitador.verificar("auth:1.1.1.1", 2, 60)) == (True, 0)

    cliente.zcard = AsyncMock(return_value=2)
    cliente.zrange = AsyncMock(return_value=[("t", 100.0)])
    ok, retry = await limitador.verificar("auth:1.1.1.1", 2, 60)
    assert not ok
    assert retry >= 1
    await limitador.fechar()
    cliente.aclose.assert_awaited()
