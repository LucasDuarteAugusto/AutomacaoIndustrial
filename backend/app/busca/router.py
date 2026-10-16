from fastapi import APIRouter

from app.busca.deps import BuscaServiceDep
from app.busca.schemas import BuscaOut, BuscaRequest

router = APIRouter(prefix="/v1/busca", tags=["busca"])


@router.post("")
async def buscar(dados: BuscaRequest, service: BuscaServiceDep) -> BuscaOut:
    return await service.buscar(dados)
