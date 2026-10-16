from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogo.repository import FamiliaRepository
from app.core.errors import Conflito, NaoEncontrado, RegraNegocio
from app.core.schemas import Pagina
from app.core.servicos import aplicar_alteracoes, remover_ou_conflito
from app.documentos.models import Idioma
from app.documentos.repository import DocumentoRepository
from app.falhas.models import Falha, TipoFalha
from app.falhas.repository import FalhaRepository
from app.falhas.schemas import FalhaCreate, FalhaOut, FalhaUpdate


def _firmware_ou_none(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpo = valor.strip()
    return limpo or None


class FalhaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.falhas = FalhaRepository(session)
        self.familias = FamiliaRepository(session)
        self.documentos = DocumentoRepository(session)

    async def _obter(self, id_falha: UUID) -> Falha:
        falha = await self.falhas.obter(id_falha)
        if falha is None:
            raise NaoEncontrado(f"Falha {id_falha} não encontrada.")
        return falha

    async def _validar_referencias(self, id_familia: UUID | None, id_documento: UUID | None) -> None:
        if id_familia is not None and await self.familias.obter(id_familia) is None:
            raise RegraNegocio(f"Família {id_familia} não encontrada.")
        if id_documento is not None and await self.documentos.obter(id_documento) is None:
            raise RegraNegocio(f"Documento {id_documento} não encontrado.")

    async def listar(
        self,
        *,
        id_familia: UUID | None,
        codigo: str | None,
        tipo: TipoFalha | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> Pagina[FalhaOut]:
        itens, total = await self.falhas.listar(
            id_familia=id_familia,
            codigo=codigo,
            tipo=tipo,
            versao_firmware=_firmware_ou_none(versao_firmware),
            idioma=idioma,
            busca=busca,
            ativo=ativo,
            limit=limit,
            offset=offset,
        )
        return Pagina(items=[FalhaOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_falha: UUID) -> FalhaOut:
        return FalhaOut.model_validate(await self._obter(id_falha))

    async def criar(self, dados: FalhaCreate) -> FalhaOut:
        await self._validar_referencias(dados.id_familia, dados.id_documento)
        firmware = _firmware_ou_none(dados.versao_firmware)
        if await self.falhas.codigo_em_uso(
            id_familia=dados.id_familia,
            codigo=dados.codigo,
            idioma=dados.idioma,
            versao_firmware=firmware,
        ):
            raise Conflito(f"Já existe falha '{dados.codigo}' nesta família/idioma/firmware.")
        payload = dados.model_dump()
        payload["versao_firmware"] = firmware
        falha = await self.falhas.adicionar(Falha(**payload))
        await self.session.commit()
        return FalhaOut.model_validate(falha)

    async def alterar(self, id_falha: UUID, dados: FalhaUpdate) -> FalhaOut:
        falha = await self._obter(id_falha)
        id_familia = dados.id_familia if dados.id_familia is not None else falha.id_familia
        idioma = dados.idioma if dados.idioma is not None else falha.idioma
        codigo = dados.codigo if dados.codigo is not None else falha.codigo
        if "versao_firmware" in dados.model_fields_set:
            firmware = _firmware_ou_none(dados.versao_firmware)
        else:
            firmware = falha.versao_firmware
        await self._validar_referencias(
            dados.id_familia,
            dados.id_documento if "id_documento" in dados.model_fields_set else None,
        )
        if await self.falhas.codigo_em_uso(
            id_familia=id_familia,
            codigo=codigo,
            idioma=idioma,
            versao_firmware=firmware,
            ignorar_id=id_falha,
        ):
            raise Conflito(f"Já existe falha '{codigo}' nesta família/idioma/firmware.")
        aplicar_alteracoes(falha, dados)
        if "versao_firmware" in dados.model_fields_set:
            falha.versao_firmware = firmware
        await self.session.commit()
        return FalhaOut.model_validate(falha)

    async def excluir(self, id_falha: UUID) -> None:
        falha = await self._obter(id_falha)
        await remover_ou_conflito(
            self.session,
            self.falhas,
            falha,
            "Não foi possível excluir a falha.",
        )

    async def buscar_por_codigos(
        self,
        *,
        codigos: list[str],
        id_familia: UUID | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
    ) -> list[FalhaOut]:
        itens = await self.falhas.buscar_por_codigos(
            codigos=codigos,
            id_familia=id_familia,
            versao_firmware=_firmware_ou_none(versao_firmware),
            idioma=idioma,
        )
        return [FalhaOut.model_validate(i) for i in itens]
