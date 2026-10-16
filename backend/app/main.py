from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agente.router import router as agente_router
from app.armazenamento.factory import criar_armazenamento
from app.auth.router import router as auth_router
from app.busca.router import router as busca_router
from app.catalogo.router import routers as catalogo_routers
from app.core.config import Settings, get_settings
from app.core.db import criar_engine, criar_sessionmaker
from app.core.handlers import registrar_handlers
from app.core.logging import configurar_logging
from app.core.rate_limit import RateLimitMiddleware, criar_limitador
from app.documentos.router import router as documentos_router
from app.falhas.router import router as falhas_router
from app.health.router import router as health_router
from app.ia.embedding import criar_provedor_embedding
from app.ia.fake import EmbeddingFake, LLMFake
from app.ia.llm import criar_provedor_llm
from app.parametros.router import router as parametros_router

log = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configurar_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = criar_engine(settings)
        app.state.settings = settings
        app.state.engine = engine
        app.state.sessionmaker = criar_sessionmaker(engine)
        async with httpx.AsyncClient() as cliente_http:
            app.state.http_client = cliente_http
            if settings.ambiente == "teste":
                app.state.provedor_embedding = EmbeddingFake(settings.embedding_dimensao)
                app.state.provedor_llm = LLMFake()
            else:
                app.state.provedor_embedding = criar_provedor_embedding(settings, cliente_http)
                app.state.provedor_llm = criar_provedor_llm(settings, cliente_http)
            app.state.armazenamento = criar_armazenamento(settings)
            app.state.limitador = criar_limitador(settings)
            log.info(
                "app_iniciada",
                ambiente=settings.ambiente,
                embedding_modelo=settings.embedding_modelo if settings.ambiente != "teste" else "fake-embedding",
                embedding_dimensao=settings.embedding_dimensao,
                llm_modelo="fake-llm" if settings.ambiente == "teste" else settings.llm_modelo,
                armazenamento_tipo=settings.armazenamento_tipo,
                rate_limit_habilitado=settings.rate_limit_habilitado,
                rate_limit_backend=settings.rate_limit_backend,
            )
            yield
        await engine.dispose()
        log.info("app_encerrada")

    app = FastAPI(title=settings.nome_app, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_lista,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Rate limit por IP (memória; Redis na etapa de escala). Desligado em ambiente=teste via Settings.
    app.add_middleware(
        RateLimitMiddleware,
        settings=settings,
        limitador=criar_limitador(settings),
    )
    registrar_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    for router in (
        *catalogo_routers,
        documentos_router,
        parametros_router,
        falhas_router,
        busca_router,
        agente_router,
    ):
        app.include_router(router)
    return app
