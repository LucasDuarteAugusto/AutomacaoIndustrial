from uuid import UUID

from sqlalchemy import ColumnElement, or_, select

from app.catalogo.models import Equipamento, Familia
from app.core.repository import RepositorioBase
from app.documentos.models import Documento, Idioma, TipoDocumento


class DocumentoRepository(RepositorioBase[Documento]):
    modelo = Documento

    async def obter_por_hash(self, hash_sha256: str) -> Documento | None:
        return await self.session.scalar(select(Documento).where(Documento.hash_sha256 == hash_sha256))

    async def listar(
        self,
        id_familia: UUID | None,
        id_equipamento: UUID | None,
        tipo_documento: TipoDocumento | None,
        idioma: Idioma | None,
        busca: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Documento], int]:
        filtros: list[ColumnElement[bool]] = []
        if id_familia:
            filtros.append(Documento.familias.any(Familia.id_familia == id_familia))
        if id_equipamento:
            filtros.append(Documento.equipamentos.any(Equipamento.id_equipamento == id_equipamento))
        if tipo_documento:
            filtros.append(Documento.tipo_documento == tipo_documento)
        if idioma:
            filtros.append(Documento.idioma == idioma)
        if busca:
            filtros.append(
                or_(
                    Documento.titulo.icontains(busca, autoescape=True),
                    Documento.codigo_documento.icontains(busca, autoescape=True),
                )
            )
        return await self.paginar(filtros, [Documento.titulo, Documento.id_documento], limit, offset)
