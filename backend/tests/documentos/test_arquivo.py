import pytest

from app.core.errors import RegraNegocio
from app.documentos.arquivo import content_disposition_inline, hash_sha256, nome_arquivo_pdf, validar_pdf


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


def test_nome_arquivo_pdf_remove_separadores_e_controles() -> None:
    assert nome_arquivo_pdf('Manual\\G120/v4.7: "rampa"\n', reserva="x") == "Manual G120 v4.7 rampa.pdf"


def test_nome_arquivo_pdf_usa_reserva_quando_vazio() -> None:
    assert nome_arquivo_pdf(" / .. ", reserva="documento-1") == "documento-1.pdf"


def test_content_disposition_inline_tem_nome_ascii_e_utf8() -> None:
    assert content_disposition_inline("Lista de parâmetros.pdf") == (
        "inline; filename=\"Lista-de-parametros.pdf\"; filename*=UTF-8''Lista%20de%20par%C3%A2metros.pdf"
    )


def test_hash_sha256_estavel() -> None:
    assert hash_sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
