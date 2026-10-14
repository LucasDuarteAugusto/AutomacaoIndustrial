from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.db import criar_engine, criar_sessionmaker
from app.core.handlers import registrar_handlers
from app.core.logging import configurar_logging
from app.health.router import router as health_router

log = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configurar_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = criar_engine(settings)
        app.state.engine = engine
        app.state.sessionmaker = criar_sessionmaker(engine)
        log.info("app_iniciada", ambiente=settings.ambiente)
        yield
        await engine.dispose()
        log.info("app_encerrada")

    app = FastAPI(title=settings.nome_app, version="0.1.0", lifespan=lifespan)
    registrar_handlers(app)
    app.include_router(health_router)
    return app
