from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogo.models import Equipamento, Fabricante, Familia
from app.catalogo.repository import (
    EquipamentoRepository,
    FabricanteRepository,
    FamiliaRepository,
    TipoEquipamentoRepository,
)
from app.catalogo.schemas import (
    EquipamentoCreate,
    EquipamentoOut,
    EquipamentoUpdate,
    FabricanteCreate,
    FabricanteOut,
    FabricanteUpdate,
    FamiliaCreate,
    FamiliaOut,
    FamiliaUpdate,
    TipoEquipamentoOut,
)
from app.core.errors import Conflito, NaoEncontrado, RegraNegocio
from app.core.schemas import Pagina
from app.core.servicos import aplicar_alteracoes, remover_ou_conflito


class TipoEquipamentoService:
    def __init__(self, session: AsyncSession) -> None:
        self.tipos = TipoEquipamentoRepository(session)

    async def listar(self, limit: int, offset: int) -> Pagina[TipoEquipamentoOut]:
        itens, total = await self.tipos.listar(limit, offset)
        return Pagina(items=[TipoEquipamentoOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_tipo_equipamento: UUID) -> TipoEquipamentoOut:
        tipo = await self.tipos.obter(id_tipo_equipamento)
        if tipo is None:
            raise NaoEncontrado(f"Tipo de equipamento {id_tipo_equipamento} não encontrado.")
        return TipoEquipamentoOut.model_validate(tipo)


class FabricanteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.fabricantes = FabricanteRepository(session)

    async def _obter(self, id_fabricante: UUID) -> Fabricante:
        fabricante = await self.fabricantes.obter(id_fabricante)
        if fabricante is None:
            raise NaoEncontrado(f"Fabricante {id_fabricante} não encontrado.")
        return fabricante

    async def listar(self, busca: str | None, ativo: bool | None, limit: int, offset: int) -> Pagina[FabricanteOut]:
        itens, total = await self.fabricantes.listar(busca, ativo, limit, offset)
        return Pagina(items=[FabricanteOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_fabricante: UUID) -> FabricanteOut:
        return FabricanteOut.model_validate(await self._obter(id_fabricante))

    async def criar(self, dados: FabricanteCreate) -> FabricanteOut:
        if await self.fabricantes.nome_em_uso(dados.nome):
            raise Conflito(f"Já existe um fabricante chamado '{dados.nome}'.")
        fabricante = await self.fabricantes.adicionar(Fabricante(**dados.model_dump()))
        await self.session.commit()
        return FabricanteOut.model_validate(fabricante)

    async def alterar(self, id_fabricante: UUID, dados: FabricanteUpdate) -> FabricanteOut:
        fabricante = await self._obter(id_fabricante)
        if dados.nome is not None and await self.fabricantes.nome_em_uso(dados.nome, ignorar_id=id_fabricante):
            raise Conflito(f"Já existe um fabricante chamado '{dados.nome}'.")
        aplicar_alteracoes(fabricante, dados)
        await self.session.commit()
        return FabricanteOut.model_validate(fabricante)

    async def excluir(self, id_fabricante: UUID) -> None:
        fabricante = await self._obter(id_fabricante)
        await remover_ou_conflito(
            self.session,
            self.fabricantes,
            fabricante,
            "O fabricante possui famílias cadastradas. Desative-o (ativo=false) em vez de excluir.",
        )


class FamiliaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.familias = FamiliaRepository(session)
        self.fabricantes = FabricanteRepository(session)
        self.tipos = TipoEquipamentoRepository(session)

    async def _obter(self, id_familia: UUID) -> Familia:
        familia = await self.familias.obter(id_familia)
        if familia is None:
            raise NaoEncontrado(f"Família {id_familia} não encontrada.")
        return familia

    async def _validar_referencias(self, id_fabricante: UUID | None, id_tipo_equipamento: UUID | None) -> None:
        if id_fabricante is not None and await self.fabricantes.obter(id_fabricante) is None:
            raise RegraNegocio(f"Fabricante {id_fabricante} não existe.")
        if id_tipo_equipamento is not None and await self.tipos.obter(id_tipo_equipamento) is None:
            raise RegraNegocio(f"Tipo de equipamento {id_tipo_equipamento} não existe.")

    async def listar(
        self,
        id_fabricante: UUID | None,
        id_tipo_equipamento: UUID | None,
        busca: str | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> Pagina[FamiliaOut]:
        itens, total = await self.familias.listar(id_fabricante, id_tipo_equipamento, busca, ativo, limit, offset)
        return Pagina(items=[FamiliaOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_familia: UUID) -> FamiliaOut:
        return FamiliaOut.model_validate(await self._obter(id_familia))

    async def criar(self, dados: FamiliaCreate) -> FamiliaOut:
        await self._validar_referencias(dados.id_fabricante, dados.id_tipo_equipamento)
        if await self.familias.nome_em_uso(dados.id_fabricante, dados.nome):
            raise Conflito(f"O fabricante já possui uma família chamada '{dados.nome}'.")
        familia = await self.familias.adicionar(Familia(**dados.model_dump()))
        await self.session.commit()
        return FamiliaOut.model_validate(familia)

    async def alterar(self, id_familia: UUID, dados: FamiliaUpdate) -> FamiliaOut:
        familia = await self._obter(id_familia)
        await self._validar_referencias(dados.id_fabricante, dados.id_tipo_equipamento)
        id_fabricante = dados.id_fabricante or familia.id_fabricante
        nome = dados.nome or familia.nome
        if await self.familias.nome_em_uso(id_fabricante, nome, ignorar_id=id_familia):
            raise Conflito(f"O fabricante já possui uma família chamada '{nome}'.")
        aplicar_alteracoes(familia, dados)
        await self.session.commit()
        return FamiliaOut.model_validate(familia)

    async def excluir(self, id_familia: UUID) -> None:
        familia = await self._obter(id_familia)
        await remover_ou_conflito(
            self.session,
            self.familias,
            familia,
            "A família possui equipamentos ou documentos vinculados. Desative-a (ativo=false) em vez de excluir.",
        )


class EquipamentoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.equipamentos = EquipamentoRepository(session)
        self.familias = FamiliaRepository(session)

    async def _obter(self, id_equipamento: UUID) -> Equipamento:
        equipamento = await self.equipamentos.obter(id_equipamento)
        if equipamento is None:
            raise NaoEncontrado(f"Equipamento {id_equipamento} não encontrado.")
        return equipamento

    async def listar(
        self, id_familia: UUID | None, busca: str | None, ativo: bool | None, limit: int, offset: int
    ) -> Pagina[EquipamentoOut]:
        itens, total = await self.equipamentos.listar(id_familia, busca, ativo, limit, offset)
        return Pagina(items=[EquipamentoOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_equipamento: UUID) -> EquipamentoOut:
        return EquipamentoOut.model_validate(await self._obter(id_equipamento))

    async def criar(self, dados: EquipamentoCreate) -> EquipamentoOut:
        if await self.familias.obter(dados.id_familia) is None:
            raise RegraNegocio(f"Família {dados.id_familia} não existe.")
        if await self.equipamentos.codigo_em_uso(dados.id_familia, dados.codigo_pedido):
            raise Conflito(f"A família já possui um equipamento com o código '{dados.codigo_pedido}'.")
        equipamento = await self.equipamentos.adicionar(Equipamento(**dados.model_dump()))
        await self.session.commit()
        return EquipamentoOut.model_validate(equipamento)

    async def alterar(self, id_equipamento: UUID, dados: EquipamentoUpdate) -> EquipamentoOut:
        equipamento = await self._obter(id_equipamento)
        if dados.id_familia is not None and await self.familias.obter(dados.id_familia) is None:
            raise RegraNegocio(f"Família {dados.id_familia} não existe.")
        id_familia = dados.id_familia or equipamento.id_familia
        codigo = dados.codigo_pedido or equipamento.codigo_pedido
        if await self.equipamentos.codigo_em_uso(id_familia, codigo, ignorar_id=id_equipamento):
            raise Conflito(f"A família já possui um equipamento com o código '{codigo}'.")
        aplicar_alteracoes(equipamento, dados)
        await self.session.commit()
        return EquipamentoOut.model_validate(equipamento)

    async def excluir(self, id_equipamento: UUID) -> None:
        equipamento = await self._obter(id_equipamento)
        await remover_ou_conflito(
            self.session,
            self.equipamentos,
            equipamento,
            "O equipamento possui documentos vinculados. Desative-o (ativo=false) em vez de excluir.",
        )
