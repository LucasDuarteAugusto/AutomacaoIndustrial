from fastapi import APIRouter, Depends

from app.auth.deps import exigir_usuario
from app.busca.deps import BuscaServiceDep
from app.busca.schemas import BuscaOut, BuscaRequest

router = APIRouter(prefix="/v1/busca", tags=["busca"], dependencies=[Depends(exigir_usuario)])


@router.post("")
async def buscar(dados: BuscaRequest, service: BuscaServiceDep) -> BuscaOut:
    return await service.buscar(dados)
