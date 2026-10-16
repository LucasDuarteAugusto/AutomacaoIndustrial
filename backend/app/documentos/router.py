from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile, status

from app.core.deps import SettingsDep
from app.core.errors import RegraNegocio
from app.core.schemas import Pagina, PaginacaoDep
from app.documentos.deps import DocumentoServiceDep
from app.documentos.models import Idioma, TipoDocumento
from app.documentos.schemas import DocumentoCreate, DocumentoOut, DocumentoUpdate

router = APIRouter(prefix="/v1/documentos", tags=["documentos"])


@router.get("")
async def listar_documentos(
    service: DocumentoServiceDep,
    pagina: PaginacaoDep,
    id_familia: UUID | None = None,
    id_equipamento: UUID | None = None,
    tipo_documento: TipoDocumento | None = None,
    idioma: Idioma | None = None,
    busca: Annotated[str | None, Query(max_length=100, description="Texto contido no título ou código")] = None,
) -> Pagina[DocumentoOut]:
    return await service.listar(id_familia, id_equipamento, tipo_documento, idioma, busca, pagina.limit, pagina.offset)


@router.get("/{id_documento}")
async def obter_documento(id_documento: UUID, service: DocumentoServiceDep) -> DocumentoOut:
    return await service.obter(id_documento)


@router.post("", status_code=status.HTTP_201_CREATED)
async def criar_documento(dados: DocumentoCreate, service: DocumentoServiceDep) -> DocumentoOut:
    return await service.criar(dados)


@router.post("/{id_documento}/arquivo")
async def enviar_arquivo_documento(
    id_documento: UUID,
    service: DocumentoServiceDep,
    settings: SettingsDep,
    arquivo: Annotated[UploadFile, File(description="PDF do manual ou lista de parâmetros")],
) -> DocumentoOut:
    limite = settings.armazenamento_tamanho_max_bytes
    # +1 para detectar overflow sem carregar o arquivo inteiro além do limite
    conteudo = await arquivo.read(limite + 1)
    if len(conteudo) > limite:
        raise RegraNegocio(f"Arquivo excede o limite de {limite} bytes.")
    return await service.enviar_arquivo(id_documento, conteudo)


@router.patch("/{id_documento}")
async def alterar_documento(id_documento: UUID, dados: DocumentoUpdate, service: DocumentoServiceDep) -> DocumentoOut:
    return await service.alterar(id_documento, dados)


@router.delete("/{id_documento}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_documento(id_documento: UUID, service: DocumentoServiceDep) -> None:
    await service.excluir(id_documento)
