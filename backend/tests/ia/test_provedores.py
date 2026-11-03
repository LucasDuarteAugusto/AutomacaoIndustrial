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


def _resposta_embedding(vetor: list[float], quantidade: int = 1) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "object": "list",
            "data": [
                {
                    "object": "list",
                    "data": [
                        {"object": "embedding", "embedding": vetor, "index": indice} for indice in range(quantidade)
                    ],
                    "index": 0,
                }
            ],
            "model": "voyage-context-4",
            "usage": {"total_tokens": 3},
        },
    )


@pytest.mark.asyncio
async def test_voyage_divide_lote_que_excede_contexto() -> None:
    lotes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        corpo = request.read().decode()
        quantidade = corpo.count('"texto')
        lotes.append(quantidade)
        if quantidade > 2:
            return httpx.Response(
                400,
                json={
                    "detail": (
                        "The example at index 0 in your batch has too many tokens and does not fit "
                        "into the model's context window of 32000 tokens."
                    )
                },
            )
        return _resposta_embedding([0.1] * EMBEDDING_DIMENSAO_PADRAO, quantidade)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = VoyageEmbedding(_settings(voyage_api_key=SecretStr("teste")), cliente)
        vetores = await provedor.embed_documento([f"texto {i}" for i in range(4)])

    assert len(vetores) == 4
    assert lotes == [4, 2, 2]


@pytest.mark.asyncio
async def test_voyage_trecho_unico_grande_explica_limite() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "does not fit into the model's context window"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = VoyageEmbedding(_settings(voyage_api_key=SecretStr("teste")), cliente)
        with pytest.raises(ServicoIndisponivel, match="contexto"):
            await provedor.embed_documento(["um único trecho enorme"])


@pytest.mark.asyncio
async def test_voyage_retenta_429_e_conclui() -> None:
    chamadas = 0
    vetor = [0.3] * EMBEDDING_DIMENSAO_PADRAO

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"detail": "reduced rate limits"})
        return _resposta_embedding(vetor)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = VoyageEmbedding(
            _settings(voyage_api_key=SecretStr("teste"), voyage_max_tentativas=3),
            cliente,
        )
        assert await provedor.embed_consulta("rampa") == vetor
    assert chamadas == 2


@pytest.mark.asyncio
async def test_voyage_429_esgotado_explica_rate_limit() -> None:
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        return httpx.Response(429, json={"detail": "reduced rate limits"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = VoyageEmbedding(
            _settings(voyage_api_key=SecretStr("teste"), voyage_max_tentativas=2, voyage_espera_base_segundos=0),
            cliente,
        )
        with pytest.raises(ServicoIndisponivel, match="rate limit"):
            await provedor.embed_consulta("rampa")
    assert chamadas == 2


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
async def test_openai_retenta_503_e_conclui() -> None:
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        if chamadas < 3:
            return httpx.Response(503, json={"error": {"code": 503, "message": "high demand"}})
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = OpenAILLM(
            _settings(openai_api_key=SecretStr("teste"), llm_max_tentativas=3, llm_espera_base_segundos=0),
            cliente,
        )
        assert await provedor.completar(sistema="s", usuario="u") == "ok"
    assert chamadas == 3


@pytest.mark.asyncio
async def test_openai_503_esgotado_explica_sobrecarga() -> None:
    chamadas = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal chamadas
        chamadas += 1
        return httpx.Response(503, json={"error": {"code": 503, "message": "high demand"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = OpenAILLM(
            _settings(openai_api_key=SecretStr("teste"), llm_max_tentativas=2, llm_espera_base_segundos=0),
            cliente,
        )
        with pytest.raises(ServicoIndisponivel, match="sobrecarregado"):
            await provedor.completar(sistema="s", usuario="u")
    assert chamadas == 2


@pytest.mark.asyncio
async def test_openai_modelo_inexistente_explica_configuracao() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "model not found"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as cliente:
        provedor = OpenAILLM(_settings(openai_api_key=SecretStr("teste"), llm_modelo="gemini-2.5-flash"), cliente)
        with pytest.raises(ServicoIndisponivel, match="LLM_MODELO") as erro:
            await provedor.completar(sistema="s", usuario="u")
    assert "gemini-2.5-flash" in str(erro.value)


@pytest.mark.asyncio
async def test_openai_sem_chave_levanta_servico_indisponivel() -> None:
    async with httpx.AsyncClient() as cliente:
        provedor = OpenAILLM(_settings(), cliente)
        with pytest.raises(ServicoIndisponivel, match="OPENAI_API_KEY"):
            await provedor.completar(sistema="s", usuario="u")
