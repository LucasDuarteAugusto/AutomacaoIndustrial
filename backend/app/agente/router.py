from fastapi import APIRouter, Depends

from app.agente.deps import AgenteServiceDep
from app.agente.schemas import AgentePerguntaRequest, AgenteRespostaOut
from app.auth.deps import exigir_usuario

router = APIRouter(prefix="/v1/agente", tags=["agente"], dependencies=[Depends(exigir_usuario)])


@router.post("/perguntar", response_model=AgenteRespostaOut)
async def perguntar(dados: AgentePerguntaRequest, service: AgenteServiceDep) -> AgenteRespostaOut:
    return await service.perguntar(dados)
