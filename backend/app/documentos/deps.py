from typing import Annotated

from fastapi import Depends

from app.armazenamento.deps import ArmazenamentoDep
from app.core.deps import SessionDep, SettingsDep
from app.documentos.service import DocumentoService
from app.ia.deps import ProvedorEmbeddingDep


def get_documento_service(
    session: SessionDep,
    armazenamento: ArmazenamentoDep,
    embedding: ProvedorEmbeddingDep,
    settings: SettingsDep,
) -> DocumentoService:
    return DocumentoService(session, armazenamento, embedding, settings)


DocumentoServiceDep = Annotated[DocumentoService, Depends(get_documento_service)]
