from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.documentos.service import DocumentoService


def get_documento_service(session: SessionDep) -> DocumentoService:
    return DocumentoService(session)


DocumentoServiceDep = Annotated[DocumentoService, Depends(get_documento_service)]
