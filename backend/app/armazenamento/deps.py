from typing import Annotated, cast

from fastapi import Depends, Request

from app.armazenamento.base import ArmazenamentoArquivos


def get_armazenamento(request: Request) -> ArmazenamentoArquivos:
    return cast(ArmazenamentoArquivos, request.app.state.armazenamento)


ArmazenamentoDep = Annotated[ArmazenamentoArquivos, Depends(get_armazenamento)]
