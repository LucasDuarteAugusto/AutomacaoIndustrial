import pytest

from app.core.errors import RegraNegocio
from app.documentos.arquivo import hash_sha256, validar_pdf


def test_validar_pdf_ok() -> None:
    validar_pdf(b"%PDF-1.4\n%%EOF\n", tamanho_max=100)


def test_validar_pdf_vazio() -> None:
    with pytest.raises(RegraNegocio, match="vazio"):
        validar_pdf(b"")


def test_validar_pdf_assinatura() -> None:
    with pytest.raises(RegraNegocio, match="PDF"):
        validar_pdf(b"nao-pdf")


def test_validar_pdf_tamanho() -> None:
    with pytest.raises(RegraNegocio, match="limite"):
        validar_pdf(b"%PDF-" + b"x" * 20, tamanho_max=10)


def test_hash_sha256_estavel() -> None:
    assert hash_sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
