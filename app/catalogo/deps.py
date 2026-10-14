from typing import Annotated

from fastapi import Depends

from app.catalogo.service import EquipamentoService, FabricanteService, FamiliaService, TipoEquipamentoService
from app.core.deps import SessionDep


def get_tipo_equipamento_service(session: SessionDep) -> TipoEquipamentoService:
    return TipoEquipamentoService(session)


def get_fabricante_service(session: SessionDep) -> FabricanteService:
    return FabricanteService(session)


def get_familia_service(session: SessionDep) -> FamiliaService:
    return FamiliaService(session)


def get_equipamento_service(session: SessionDep) -> EquipamentoService:
    return EquipamentoService(session)


TipoEquipamentoServiceDep = Annotated[TipoEquipamentoService, Depends(get_tipo_equipamento_service)]
FabricanteServiceDep = Annotated[FabricanteService, Depends(get_fabricante_service)]
FamiliaServiceDep = Annotated[FamiliaService, Depends(get_familia_service)]
EquipamentoServiceDep = Annotated[EquipamentoService, Depends(get_equipamento_service)]
