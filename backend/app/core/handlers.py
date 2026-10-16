from http import HTTPStatus
from typing import Any, cast

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import ErroDominio, LimiteExcedido

PROBLEM_JSON = "application/problem+json"

log = structlog.get_logger()


def problema(
    request: Request,
    status: int,
    titulo: str,
    detalhe: str | None = None,
    tipo: str = "about:blank",
    **extras: Any,
) -> JSONResponse:
    corpo: dict[str, Any] = {
        "type": tipo,
        "title": titulo,
        "status": status,
        "detail": detalhe,
        "instance": request.url.path,
        **extras,
    }
    return JSONResponse(jsonable_encoder(corpo), status_code=status, media_type=PROBLEM_JSON)


async def _erro_dominio(request: Request, exc: Exception) -> JSONResponse:
    erro = cast(ErroDominio, exc)
    resposta = problema(request, erro.status, erro.titulo, erro.detalhe, erro.tipo)
    if isinstance(erro, LimiteExcedido):
        resposta.headers["Retry-After"] = str(erro.retry_after)
    return resposta


async def _erro_validacao(request: Request, exc: Exception) -> JSONResponse:
    erro = cast(RequestValidationError, exc)
    return problema(
        request,
        HTTPStatus.UNPROCESSABLE_CONTENT,
        "Dados de entrada inválidos",
        "Um ou mais campos não passaram na validação.",
        errors=erro.errors(),
    )


async def _erro_http(request: Request, exc: Exception) -> JSONResponse:
    erro = cast(StarletteHTTPException, exc)
    titulo = HTTPStatus(erro.status_code).phrase
    detalhe = str(erro.detail) if erro.detail != titulo else None
    return problema(request, erro.status_code, titulo, detalhe)


async def _erro_integridade(request: Request, exc: Exception) -> JSONResponse:
    log.warning("violacao_integridade", path=request.url.path, erro=str(cast(IntegrityError, exc).orig))
    return problema(request, HTTPStatus.CONFLICT, "Conflito", "A operação viola uma restrição de integridade do banco.")


async def _erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    log.exception("erro_nao_tratado", path=request.url.path)
    return problema(request, HTTPStatus.INTERNAL_SERVER_ERROR, "Erro interno")


def registrar_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ErroDominio, _erro_dominio)
    app.add_exception_handler(RequestValidationError, _erro_validacao)
    app.add_exception_handler(StarletteHTTPException, _erro_http)
    app.add_exception_handler(IntegrityError, _erro_integridade)
    app.add_exception_handler(Exception, _erro_inesperado)
