from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI

from app.catalogo.router import routers as catalogo_routers
from app.core.config import Settings, get_settings
from app.core.db import criar_engine, criar_sessionmaker
from app.core.handlers import registrar_handlers
from app.core.logging import configurar_logging
from app.documentos.router import router as documentos_router
from app.health.router import router as health_router
from app.ia.embedding import criar_provedor_embedding
from app.ia.llm import criar_provedor_llm

log = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configurar_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = criar_engine(settings)
        app.state.engine = engine
        app.state.sessionmaker = criar_sessionmaker(engine)
        async with httpx.AsyncClient() as cliente_http:
            app.state.http_client = cliente_http
            app.state.provedor_embedding = criar_provedor_embedding(settings, cliente_http)
            app.state.provedor_llm = criar_provedor_llm(settings, cliente_http)
            log.info(
                "app_iniciada",
                ambiente=settings.ambiente,
                embedding_modelo=settings.embedding_modelo,
                embedding_dimensao=settings.embedding_dimensao,
                llm_modelo=settings.llm_modelo,
            )
            yield
        await engine.dispose()
        log.info("app_encerrada")

    app = FastAPI(title=settings.nome_app, version="0.1.0", lifespan=lifespan)
    registrar_handlers(app)
    app.include_router(health_router)
    for router in (*catalogo_routers, documentos_router):
        app.include_router(router)
    return app
