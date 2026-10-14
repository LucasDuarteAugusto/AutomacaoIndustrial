from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.db import banco_disponivel
from app.core.errors import ServicoIndisponivel

router = APIRouter(tags=["health"])


class StatusOut(BaseModel):
    status: str


@router.get("/health")
async def health() -> StatusOut:
    return StatusOut(status="ok")


@router.get("/ready")
async def ready(request: Request) -> StatusOut:
    engine: AsyncEngine = request.app.state.engine
    if not await banco_disponivel(engine):
        raise ServicoIndisponivel("Banco de dados não está acessível.")
    return StatusOut(status="ok")
