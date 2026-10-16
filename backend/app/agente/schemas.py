from uuid import UUID

from pydantic import Field

from app.core.schemas import Entrada, Saida
from app.documentos.models import Idioma, TipoDocumento


class AgentePerguntaRequest(Entrada):
    pergunta: str = Field(min_length=1, max_length=2000, description="Pergunta em linguagem natural")
    limit: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Quantidade máxima de trechos recuperados para o contexto do LLM",
    )
    id_fabricante: UUID | None = None
    id_familia: UUID | None = None
    id_equipamento: UUID | None = None
    tipo_documento: TipoDocumento | None = None
    idioma: Idioma | None = None
    versao_firmware: str | None = Field(default=None, max_length=30)


class CitacaoOut(Saida):
    indice: int = Field(description="Número da fonte no contexto ([1], [2], …)")
    id_trecho: UUID
    id_documento: UUID
    titulo_documento: str
    codigo_documento: str | None
    secao: str | None
    pagina: int | None
    trecho: str = Field(description="Conteúdo do trecho usado no contexto")
    score: float


class AgenteRespostaOut(Saida):
    pergunta: str
    resposta: str
    citacoes: list[CitacaoOut]
    modelo_llm: str
    trechos_consultados: int
