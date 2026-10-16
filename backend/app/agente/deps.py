from typing import Annotated

from fastapi import Depends

from app.agente.service import AgenteService
from app.busca.deps import BuscaServiceDep
from app.ia.deps import ProvedorLLMDep


def get_agente_service(busca: BuscaServiceDep, llm: ProvedorLLMDep) -> AgenteService:
    return AgenteService(busca, llm)


AgenteServiceDep = Annotated[AgenteService, Depends(get_agente_service)]
