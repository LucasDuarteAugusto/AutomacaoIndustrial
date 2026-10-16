from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.falhas.service import FalhaService


def get_falha_service(session: SessionDep) -> FalhaService:
    return FalhaService(session)


FalhaServiceDep = Annotated[FalhaService, Depends(get_falha_service)]
