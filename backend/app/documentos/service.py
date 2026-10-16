from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.armazenamento.base import ArmazenamentoArquivos
from app.armazenamento.chave import chave_documento
from app.catalogo.models import Equipamento, Familia
from app.catalogo.repository import EquipamentoRepository, FamiliaRepository
from app.core.config import Settings
from app.core.errors import Conflito, NaoEncontrado, RegraNegocio
from app.core.schemas import Pagina
from app.core.servicos import aplicar_alteracoes
from app.documentos.arquivo import hash_sha256, validar_pdf
from app.documentos.models import Documento, Idioma, StatusProcessamento, TipoDocumento
from app.documentos.repository import DocumentoRepository
from app.documentos.schemas import DocumentoCreate, DocumentoOut, DocumentoUpdate
from app.trechos.models import Trecho

CAMPOS_VINCULO = {"ids_familias", "ids_equipamentos"}


def _sem_repetidos(ids: Sequence[UUID]) -> list[UUID]:
    return list(dict.fromkeys(ids))


class DocumentoService:
    def __init__(self, session: AsyncSession, armazenamento: ArmazenamentoArquivos, settings: Settings) -> None:
        self.session = session
        self.armazenamento = armazenamento
        self.settings = settings
        self.documentos = DocumentoRepository(session)
        self.familias = FamiliaRepository(session)
        self.equipamentos = EquipamentoRepository(session)

    async def _obter(self, id_documento: UUID) -> Documento:
        documento = await self.documentos.obter(id_documento)
        if documento is None:
            raise NaoEncontrado(f"Documento {id_documento} não encontrado.")
        return documento

    async def _carregar_familias(self, ids: Sequence[UUID]) -> list[Familia]:
        ids = _sem_repetidos(ids)
        familias = await self.familias.obter_varios(ids)
        faltando = set(ids) - {f.id_familia for f in familias}
        if faltando:
            raise RegraNegocio(f"Família(s) inexistente(s): {', '.join(sorted(map(str, faltando)))}.")
        return familias

    async def _carregar_equipamentos(self, ids: Sequence[UUID], familias: Sequence[Familia]) -> list[Equipamento]:
        ids = _sem_repetidos(ids)
        equipamentos = await self.equipamentos.obter_varios(ids)
        faltando = set(ids) - {e.id_equipamento for e in equipamentos}
        if faltando:
            raise RegraNegocio(f"Equipamento(s) inexistente(s): {', '.join(sorted(map(str, faltando)))}.")
        ids_familias = {f.id_familia for f in familias}
        fora = [e.codigo_pedido for e in equipamentos if e.id_familia not in ids_familias]
        if fora:
            raise RegraNegocio(f"Equipamento(s) {', '.join(fora)} não pertencem às famílias vinculadas ao documento.")
        return equipamentos

    async def _apagar_arquivo_se_houver(self, chave: str | None) -> None:
        if chave:
            await self.armazenamento.apagar(chave)

    async def _limpar_trechos(self, id_documento: UUID) -> None:
        await self.session.execute(delete(Trecho).where(Trecho.id_documento == id_documento))

    async def listar(
        self,
        id_familia: UUID | None,
        id_equipamento: UUID | None,
        tipo_documento: TipoDocumento | None,
        idioma: Idioma | None,
        busca: str | None,
        limit: int,
        offset: int,
    ) -> Pagina[DocumentoOut]:
        itens, total = await self.documentos.listar(
            id_familia, id_equipamento, tipo_documento, idioma, busca, limit, offset
        )
        return Pagina(items=[DocumentoOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_documento: UUID) -> DocumentoOut:
        return DocumentoOut.model_validate(await self._obter(id_documento))

    async def criar(self, dados: DocumentoCreate) -> DocumentoOut:
        familias = await self._carregar_familias(dados.ids_familias)
        equipamentos = await self._carregar_equipamentos(dados.ids_equipamentos, familias)
        documento = Documento(**dados.model_dump(exclude=CAMPOS_VINCULO), familias=familias, equipamentos=equipamentos)
        await self.documentos.adicionar(documento)
        await self.session.commit()
        return DocumentoOut.model_validate(documento)

    async def alterar(self, id_documento: UUID, dados: DocumentoUpdate) -> DocumentoOut:
        documento = await self._obter(id_documento)
        familias = (
            await self._carregar_familias(dados.ids_familias) if dados.ids_familias is not None else documento.familias
        )
        ids_equipamentos = (
            dados.ids_equipamentos
            if dados.ids_equipamentos is not None
            else [e.id_equipamento for e in documento.equipamentos]
        )
        documento.equipamentos = await self._carregar_equipamentos(ids_equipamentos, familias)
        documento.familias = list(familias)
        aplicar_alteracoes(documento, dados, ignorar=CAMPOS_VINCULO)
        await self.session.commit()
        return DocumentoOut.model_validate(documento)

    async def enviar_arquivo(self, id_documento: UUID, conteudo: bytes) -> DocumentoOut:
        validar_pdf(conteudo, tamanho_max=self.settings.armazenamento_tamanho_max_bytes)
        digest = hash_sha256(conteudo)
        documento = await self._obter(id_documento)

        if (
            documento.hash_sha256 == digest
            and documento.chave_arquivo
            and await self.armazenamento.existe(documento.chave_arquivo)
        ):
            return DocumentoOut.model_validate(documento)

        outro = await self.documentos.obter_por_hash(digest)
        if outro is not None and outro.id_documento != id_documento:
            raise Conflito(f"Já existe um documento com este arquivo (hash {digest[:12]}…).")

        chave_antiga = documento.chave_arquivo
        chave_nova = chave_documento(id_documento, digest)
        await self.armazenamento.salvar(chave_nova, conteudo, content_type="application/pdf")

        if chave_antiga and chave_antiga != chave_nova:
            await self._apagar_arquivo_se_houver(chave_antiga)
            await self._limpar_trechos(id_documento)

        documento.chave_arquivo = chave_nova
        documento.hash_sha256 = digest
        documento.tamanho_bytes = len(conteudo)
        documento.status_processamento = StatusProcessamento.PENDENTE
        documento.erro_processamento = None
        # paginas preenchidas na ingestão (pipeline de trechos)
        await self.session.commit()
        return DocumentoOut.model_validate(documento)

    async def excluir(self, id_documento: UUID) -> None:
        documento = await self._obter(id_documento)
        chave = documento.chave_arquivo
        await self.documentos.remover(documento)
        await self.session.commit()
        await self._apagar_arquivo_se_houver(chave)
