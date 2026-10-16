from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogo.repository import FamiliaRepository
from app.core.errors import Conflito, NaoEncontrado, RegraNegocio
from app.core.schemas import Pagina
from app.core.servicos import aplicar_alteracoes, remover_ou_conflito
from app.documentos.models import Idioma
from app.documentos.repository import DocumentoRepository
from app.parametros.models import Parametro
from app.parametros.repository import ParametroRepository
from app.parametros.schemas import ParametroCreate, ParametroOut, ParametroUpdate


def _firmware_ou_none(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpo = valor.strip()
    return limpo or None


class ParametroService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.parametros = ParametroRepository(session)
        self.familias = FamiliaRepository(session)
        self.documentos = DocumentoRepository(session)

    async def _obter(self, id_parametro: UUID) -> Parametro:
        parametro = await self.parametros.obter(id_parametro)
        if parametro is None:
            raise NaoEncontrado(f"Parâmetro {id_parametro} não encontrado.")
        return parametro

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
        versao_firmware: str | None,
        idioma: Idioma | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> Pagina[ParametroOut]:
        itens, total = await self.parametros.listar(
            id_familia=id_familia,
            codigo=codigo,
            versao_firmware=_firmware_ou_none(versao_firmware),
            idioma=idioma,
            busca=busca,
            ativo=ativo,
            limit=limit,
            offset=offset,
        )
        return Pagina(items=[ParametroOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_parametro: UUID) -> ParametroOut:
        return ParametroOut.model_validate(await self._obter(id_parametro))

    async def criar(self, dados: ParametroCreate) -> ParametroOut:
        await self._validar_referencias(dados.id_familia, dados.id_documento)
        firmware = _firmware_ou_none(dados.versao_firmware)
        if await self.parametros.codigo_em_uso(
            id_familia=dados.id_familia,
            codigo=dados.codigo,
            idioma=dados.idioma,
            versao_firmware=firmware,
        ):
            raise Conflito(f"Já existe parâmetro '{dados.codigo}' nesta família/idioma/firmware.")
        payload = dados.model_dump()
        payload["versao_firmware"] = firmware
        parametro = await self.parametros.adicionar(Parametro(**payload))
        await self.session.commit()
        return ParametroOut.model_validate(parametro)

    async def alterar(self, id_parametro: UUID, dados: ParametroUpdate) -> ParametroOut:
        parametro = await self._obter(id_parametro)
        id_familia = dados.id_familia if dados.id_familia is not None else parametro.id_familia
        idioma = dados.idioma if dados.idioma is not None else parametro.idioma
        codigo = dados.codigo if dados.codigo is not None else parametro.codigo
        if "versao_firmware" in dados.model_fields_set:
            firmware = _firmware_ou_none(dados.versao_firmware)
        else:
            firmware = parametro.versao_firmware
        await self._validar_referencias(
            dados.id_familia,
            dados.id_documento if "id_documento" in dados.model_fields_set else None,
        )
        if await self.parametros.codigo_em_uso(
            id_familia=id_familia,
            codigo=codigo,
            idioma=idioma,
            versao_firmware=firmware,
            ignorar_id=id_parametro,
        ):
            raise Conflito(f"Já existe parâmetro '{codigo}' nesta família/idioma/firmware.")
        aplicar_alteracoes(parametro, dados)
        if "versao_firmware" in dados.model_fields_set:
            parametro.versao_firmware = firmware
        await self.session.commit()
        return ParametroOut.model_validate(parametro)

    async def excluir(self, id_parametro: UUID) -> None:
        parametro = await self._obter(id_parametro)
        await remover_ou_conflito(
            self.session,
            self.parametros,
            parametro,
            "Não foi possível excluir o parâmetro.",
        )

    async def buscar_por_codigos(
        self,
        *,
        codigos: list[str],
        id_familia: UUID | None,
        versao_firmware: str | None,
        idioma: Idioma | None,
    ) -> list[ParametroOut]:
        itens = await self.parametros.buscar_por_codigos(
            codigos=codigos,
            id_familia=id_familia,
            versao_firmware=_firmware_ou_none(versao_firmware),
            idioma=idioma,
        )
        return [ParametroOut.model_validate(i) for i in itens]
