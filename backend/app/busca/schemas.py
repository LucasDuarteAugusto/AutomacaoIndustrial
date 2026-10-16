from uuid import UUID

from pydantic import Field

from app.core.schemas import Entrada, Saida
from app.documentos.models import Idioma, TipoDocumento
from app.trechos.models import TipoConteudo


class BuscaRequest(Entrada):
    consulta: str = Field(min_length=1, max_length=2000, description="Pergunta ou termos de busca")
    limit: int = Field(default=10, ge=1, le=50, description="Quantidade máxima de trechos")
    id_fabricante: UUID | None = None
    id_familia: UUID | None = None
    id_equipamento: UUID | None = None
    tipo_documento: TipoDocumento | None = None
    idioma: Idioma | None = None
    versao_firmware: str | None = Field(default=None, max_length=30)


class TrechoBuscaOut(Saida):
    id_trecho: UUID
    id_documento: UUID
    titulo_documento: str
    tipo_documento: TipoDocumento
    idioma: Idioma
    codigo_documento: str | None
    versao_firmware: str | None
    conteudo: str
    secao: str | None
    pagina: int | None
    tipo_conteudo: TipoConteudo
    score: float
    distancia_cosseno: float | None
    rank_textual: float | None


class BuscaOut(Saida):
    consulta: str
    items: list[TrechoBuscaOut]
    total: int
