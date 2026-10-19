from collections.abc import Sequence
from dataclasses import dataclass
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
from app.documentos.arquivo import hash_sha256, nome_arquivo_pdf, validar_pdf
from app.documentos.models import Documento, Idioma, StatusProcessamento, TipoDocumento
from app.documentos.repository import DocumentoRepository
from app.documentos.schemas import DocumentoCreate, DocumentoOut, DocumentoUpdate
from app.ia.embedding import ProvedorEmbedding
from app.ingestao.pipeline import processar_documento
from app.trechos.models import Trecho

CAMPOS_VINCULO = {"ids_familias", "ids_equipamentos"}


@dataclass(frozen=True, slots=True)
class ResultadoUpload:
    documento: DocumentoOut
    agendar_ingestao: bool


@dataclass(frozen=True, slots=True)
class ArquivoDocumento:
    hash_sha256: str
    nome_arquivo: str
    conteudo: bytes | None
    """None quando o cliente já tem esta versão (If-None-Match)."""


def _sem_repetidos(ids: Sequence[UUID]) -> list[UUID]:
    return list(dict.fromkeys(ids))


class DocumentoService:
    def __init__(
        self,
        session: AsyncSession,
        armazenamento: ArmazenamentoArquivos,
        embedding: ProvedorEmbedding,
        settings: Settings,
    ) -> None:
        self.session = session
        self.armazenamento = armazenamento
        self.embedding = embedding
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
        status_processamento: StatusProcessamento | None,
        busca: str | None,
        limit: int,
        offset: int,
    ) -> Pagina[DocumentoOut]:
        itens, total = await self.documentos.listar(
            id_familia, id_equipamento, tipo_documento, idioma, status_processamento, busca, limit, offset
        )
        return Pagina(items=[DocumentoOut.model_validate(i) for i in itens], total=total)

    async def obter(self, id_documento: UUID) -> DocumentoOut:
        return DocumentoOut.model_validate(await self._obter(id_documento))

    async def obter_arquivo(self, id_documento: UUID, hashes_do_cliente: frozenset[str]) -> ArquivoDocumento:
        documento = await self._obter(id_documento)
        if not documento.chave_arquivo or not documento.hash_sha256:
            raise NaoEncontrado(f"Documento {id_documento} não possui arquivo.")
        nome = nome_arquivo_pdf(
            documento.codigo_documento or documento.titulo, reserva=f"documento-{documento.id_documento}"
        )
        if documento.hash_sha256 in hashes_do_cliente:
            return ArquivoDocumento(documento.hash_sha256, nome, conteudo=None)
        try:
            conteudo = await self.armazenamento.carregar(documento.chave_arquivo)
        except FileNotFoundError as erro:
            raise NaoEncontrado(f"Arquivo do documento {id_documento} não encontrado no armazenamento.") from erro
        return ArquivoDocumento(documento.hash_sha256, nome, conteudo)

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

    async def enviar_arquivo(self, id_documento: UUID, conteudo: bytes) -> ResultadoUpload:
        validar_pdf(conteudo, tamanho_max=self.settings.armazenamento_tamanho_max_bytes)
        digest = hash_sha256(conteudo)
        documento = await self._obter(id_documento)

        if (
            documento.hash_sha256 == digest
            and documento.chave_arquivo
            and await self.armazenamento.existe(documento.chave_arquivo)
        ):
            ja_indexado = documento.status_processamento == StatusProcessamento.INDEXADO
            return ResultadoUpload(DocumentoOut.model_validate(documento), agendar_ingestao=not ja_indexado)

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
        documento.paginas = None
        await self.session.commit()
        return ResultadoUpload(DocumentoOut.model_validate(documento), agendar_ingestao=True)

    async def preparar_reprocessamento(self, id_documento: UUID) -> DocumentoOut:
        documento = await self._obter(id_documento)
        if not documento.chave_arquivo:
            raise RegraNegocio("Documento sem arquivo para reprocessar.")
        if documento.status_processamento == StatusProcessamento.PROCESSANDO:
            raise Conflito("Documento já está em processamento.")
        documento.status_processamento = StatusProcessamento.PENDENTE
        documento.erro_processamento = None
        await self.session.commit()
        return DocumentoOut.model_validate(documento)

    async def executar_ingestao(self, id_documento: UUID) -> DocumentoOut:
        await processar_documento(
            self.session,
            armazenamento=self.armazenamento,
            embedding=self.embedding,
            settings=self.settings,
            id_documento=id_documento,
        )
        return DocumentoOut.model_validate(await self._obter(id_documento))

    async def excluir(self, id_documento: UUID) -> None:
        documento = await self._obter(id_documento)
        chave = documento.chave_arquivo
        await self.documentos.remover(documento)
        await self.session.commit()
        await self._apagar_arquivo_se_houver(chave)
