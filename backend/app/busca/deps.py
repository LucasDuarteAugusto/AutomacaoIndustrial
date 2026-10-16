from typing import Annotated

from fastapi import Depends

from app.busca.service import BuscaService
from app.core.deps import SessionDep, SettingsDep
from app.ia.deps import ProvedorEmbeddingDep


def get_busca_service(
    session: SessionDep,
    embedding: ProvedorEmbeddingDep,
    settings: SettingsDep,
) -> BuscaService:
    return BuscaService(session, embedding, settings)


BuscaServiceDep = Annotated[BuscaService, Depends(get_busca_service)]
