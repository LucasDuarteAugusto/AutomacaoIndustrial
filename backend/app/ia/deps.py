from typing import Annotated, cast

from fastapi import Depends, Request

from app.ia.embedding import ProvedorEmbedding
from app.ia.llm import ProvedorLLM


def get_provedor_embedding(request: Request) -> ProvedorEmbedding:
    return cast(ProvedorEmbedding, request.app.state.provedor_embedding)


def get_provedor_llm(request: Request) -> ProvedorLLM:
    return cast(ProvedorLLM, request.app.state.provedor_llm)


ProvedorEmbeddingDep = Annotated[ProvedorEmbedding, Depends(get_provedor_embedding)]
ProvedorLLMDep = Annotated[ProvedorLLM, Depends(get_provedor_llm)]
