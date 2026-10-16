from typing import Annotated

from fastapi import Depends

from app.agente.service import AgenteService
from app.busca.deps import BuscaServiceDep
from app.falhas.deps import FalhaServiceDep
from app.ia.deps import ProvedorLLMDep
from app.parametros.deps import ParametroServiceDep


def get_agente_service(
    busca: BuscaServiceDep,
    llm: ProvedorLLMDep,
    parametros: ParametroServiceDep,
    falhas: FalhaServiceDep,
) -> AgenteService:
    return AgenteService(busca, llm, parametros, falhas)


AgenteServiceDep = Annotated[AgenteService, Depends(get_agente_service)]
