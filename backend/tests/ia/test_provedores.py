import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import RegraNegocio, ServicoIndisponivel
from app.core.ia_defaults import EMBEDDING_DIMENSAO_PADRAO
from app.ia.embedding import VoyageEmbedding
from app.ia.llm import OpenAILLM


def _settings(**extras: object) -> Settings:
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://u:p@localhost:5433/db",
        "ambiente": "teste",
    }
    base.update(extras)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_voyage_embed_documento_e_consulta() -> None:
    dimensao = EMBEDDING_DIMENSAO_PADRAO
    vetor_doc = [0.1] * dimensao
    vetor_query = [0.2] * dimensao

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/contextualizedembeddings")
        corpo = request.read()
        assert b"voyage-context-4" in corpo
        if b'"query"' in corpo:
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {
                            "object": "list",
                            "data": [{"object": "embedding", "embedding": vetor_query, "index": 0}],
                            "index": 0,
                        }
                    ],
                    "model": "voyage-context-4",
                    "usage": {"total_tokens": 3},
                },
            )
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "object": "list",
                        "data": [
                            {"object": "embedding", "embedding": vetor_doc, "index": 0},
                            {"object": "embedding", "embedding": vetor_doc, "index": 1},
                        ],
                        "index": 0,
                    }
                ],
                "model": "voyage-context-4",
                "usage": {"total_tokens": 10},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = VoyageEmbedding(
            _settings(voyage_api_key=SecretStr("teste")),
            cliente,
        )
        docs = await provedor.embed_documento(["trecho a", "trecho b"])
        assert len(docs) == 2
        assert docs[0] == vetor_doc
        consulta = await provedor.embed_consulta("rampa de aceleração")
        assert consulta == vetor_query


@pytest.mark.asyncio
async def test_voyage_sem_chave_levanta_servico_indisponivel() -> None:
    async with httpx.AsyncClient() as cliente:
        provedor = VoyageEmbedding(_settings(), cliente)
        with pytest.raises(ServicoIndisponivel, match="VOYAGE_API_KEY"):
            await provedor.embed_consulta("teste")


@pytest.mark.asyncio
async def test_voyage_consulta_vazia_levanta_regra() -> None:
    async with httpx.AsyncClient() as cliente:
        provedor = VoyageEmbedding(_settings(voyage_api_key=SecretStr("teste")), cliente)
        with pytest.raises(RegraNegocio, match="vazia"):
            await provedor.embed_consulta("   ")


@pytest.mark.asyncio
async def test_openai_completar() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert b"gpt-5-mini" in request.read()
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"role": "assistant", "content": "Tempo de rampa padrão: 10 s."}}],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = OpenAILLM(_settings(openai_api_key=SecretStr("teste")), cliente)
        texto = await provedor.completar(sistema="Você é um assistente técnico.", usuario="Qual a rampa padrão?")
        assert "10 s" in texto


@pytest.mark.asyncio
async def test_openai_sem_chave_levanta_servico_indisponivel() -> None:
    async with httpx.AsyncClient() as cliente:
        provedor = OpenAILLM(_settings(), cliente)
        with pytest.raises(ServicoIndisponivel, match="OPENAI_API_KEY"):
            await provedor.completar(sistema="s", usuario="u")
