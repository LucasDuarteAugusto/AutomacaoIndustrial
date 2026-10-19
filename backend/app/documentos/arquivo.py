import hashlib
import re
import unicodedata
from urllib.parse import quote

from app.core.errors import RegraNegocio

ASSINATURA_PDF = b"%PDF-"
TAMANHO_MAX_PADRAO = 50 * 1024 * 1024
TAMANHO_MAX_NOME = 120

_PROIBIDOS_NO_NOME = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')
_FORA_DO_ASCII_SEGURO = re.compile(r"[^A-Za-z0-9._-]+")


def validar_pdf(conteudo: bytes, *, tamanho_max: int = TAMANHO_MAX_PADRAO) -> None:
    if not conteudo:
        raise RegraNegocio("Arquivo vazio.")
    if len(conteudo) > tamanho_max:
        raise RegraNegocio(f"Arquivo excede o limite de {tamanho_max} bytes.")
    if not conteudo.startswith(ASSINATURA_PDF):
        raise RegraNegocio("Arquivo não é um PDF válido (assinatura %PDF- ausente).")


def hash_sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def nome_arquivo_pdf(base: str, *, reserva: str) -> str:
    """Nome de download seguro (sem separadores de caminho nem caracteres de controle), com extensão .pdf."""
    limpo = " ".join(_PROIBIDOS_NO_NOME.sub(" ", base).split())[:TAMANHO_MAX_NOME].strip(" .")
    return f"{limpo or reserva}.pdf"


def content_disposition_inline(nome: str) -> str:
    """`filename` ASCII para clientes antigos e `filename*` (RFC 6266/5987) com o nome em UTF-8."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    ascii_seguro = _FORA_DO_ASCII_SEGURO.sub("-", sem_acento).strip("-") or "documento.pdf"
    return f"inline; filename=\"{ascii_seguro}\"; filename*=UTF-8''{quote(nome, safe='')}"
