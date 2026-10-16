import hashlib

from app.core.errors import RegraNegocio

ASSINATURA_PDF = b"%PDF-"
TAMANHO_MAX_PADRAO = 50 * 1024 * 1024


def validar_pdf(conteudo: bytes, *, tamanho_max: int = TAMANHO_MAX_PADRAO) -> None:
    if not conteudo:
        raise RegraNegocio("Arquivo vazio.")
    if len(conteudo) > tamanho_max:
        raise RegraNegocio(f"Arquivo excede o limite de {tamanho_max} bytes.")
    if not conteudo.startswith(ASSINATURA_PDF):
        raise RegraNegocio("Arquivo não é um PDF válido (assinatura %PDF- ausente).")


def hash_sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()
