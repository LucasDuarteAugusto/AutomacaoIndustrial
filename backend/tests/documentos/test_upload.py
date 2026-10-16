import hashlib
from uuid import UUID, uuid4

import fitz
from httpx import AsyncClient

from app.armazenamento.chave import chave_documento
from tests.factories import criar_documento


def _pdf(texto: str = "Tempo de rampa padrão: 10 s.") -> bytes:
    documento = fitz.open()
    try:
        pagina = documento.new_page()
        pagina.insert_text((72, 72), texto)
        return bytes(documento.tobytes())
    finally:
        documento.close()


PDF_MINIMO = _pdf("Conteúdo mínimo para upload.")
PDF_OUTRO = _pdf("Outro conteúdo distinto do primeiro PDF.")


async def test_upload_pdf_atualiza_metadados(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]

    resp = await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("manual.pdf", PDF_MINIMO, "application/pdf")},
    )

    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    digest = hashlib.sha256(PDF_MINIMO).hexdigest()
    assert corpo["hash_sha256"] == digest
    assert corpo["tamanho_bytes"] == len(PDF_MINIMO)
    assert corpo["chave_arquivo"] == chave_documento(UUID(id_doc), digest)
    assert corpo["status_processamento"] == "INDEXADO"
    assert corpo["erro_processamento"] is None
    assert corpo["paginas"] is not None and corpo["paginas"] >= 1


async def test_upload_idempotente_mesmo_hash(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    resp = await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    assert resp.status_code == 200
    assert resp.json()["hash_sha256"] == hashlib.sha256(PDF_MINIMO).hexdigest()
    assert resp.json()["status_processamento"] == "INDEXADO"


async def test_upload_nao_pdf_retorna_422(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    resp = await client.post(
        f"/v1/documentos/{doc['id_documento']}/arquivo",
        files={"arquivo": ("x.txt", b"nao e pdf", "text/plain")},
    )
    assert resp.status_code == 422
    assert "PDF" in resp.json()["detail"]


async def test_upload_documento_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.post(
        f"/v1/documentos/{uuid4()}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    assert resp.status_code == 404


async def test_upload_hash_de_outro_documento_retorna_409(client: AsyncClient) -> None:
    doc1 = await criar_documento(client)
    doc2 = await criar_documento(client)
    await client.post(
        f"/v1/documentos/{doc1['id_documento']}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    resp = await client.post(
        f"/v1/documentos/{doc2['id_documento']}/arquivo",
        files={"arquivo": ("b.pdf", PDF_MINIMO, "application/pdf")},
    )
    assert resp.status_code == 409
    assert "hash" in resp.json()["detail"].lower()


async def test_upload_substitui_arquivo_diferente(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    resp = await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("b.pdf", PDF_OUTRO, "application/pdf")},
    )
    assert resp.status_code == 200
    assert resp.json()["hash_sha256"] == hashlib.sha256(PDF_OUTRO).hexdigest()
    assert resp.json()["tamanho_bytes"] == len(PDF_OUTRO)
    assert resp.json()["status_processamento"] == "INDEXADO"


async def test_excluir_documento_com_arquivo_retorna_204(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("a.pdf", PDF_MINIMO, "application/pdf")},
    )
    resp = await client.delete(f"/v1/documentos/{id_doc}")
    assert resp.status_code == 204
    assert (await client.get(f"/v1/documentos/{id_doc}")).status_code == 404
