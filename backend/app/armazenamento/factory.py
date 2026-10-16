from pathlib import Path

from app.armazenamento.base import ArmazenamentoArquivos
from app.armazenamento.local import ArmazenamentoLocal
from app.armazenamento.s3 import ArmazenamentoS3
from app.core.config import Settings
from app.core.errors import RegraNegocio


def criar_armazenamento(settings: Settings) -> ArmazenamentoArquivos:
    if settings.armazenamento_tipo == "local":
        return ArmazenamentoLocal(Path(settings.armazenamento_caminho))
    if settings.armazenamento_tipo == "s3":
        return ArmazenamentoS3(settings)
    raise RegraNegocio(f"Tipo de armazenamento desconhecido: {settings.armazenamento_tipo}")
