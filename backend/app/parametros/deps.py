from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.parametros.service import ParametroService


def get_parametro_service(session: SessionDep) -> ParametroService:
    return ParametroService(session)


ParametroServiceDep = Annotated[ParametroService, Depends(get_parametro_service)]
