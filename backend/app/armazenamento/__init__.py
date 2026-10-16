"""Armazenamento de arquivos: local agora; S3-compatível (R2/AWS) quando configurado."""

from app.armazenamento.base import ArmazenamentoArquivos
from app.armazenamento.chave import chave_documento
from app.armazenamento.factory import criar_armazenamento

__all__ = ["ArmazenamentoArquivos", "chave_documento", "criar_armazenamento"]
