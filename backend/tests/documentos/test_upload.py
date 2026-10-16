import hashlib
from uuid import UUID, uuid4

from httpx import AsyncClient

from app.armazenamento.chave import chave_documento
from tests.factories import criar_documento

PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
PDF_OUTRO = b"%PDF-1.7\n1 0 obj<< /Type /Catalog >>endobj\ntrailer<<>>\n%%EOF\n"


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
    assert corpo["status_processamento"] == "PENDENTE"
    assert corpo["erro_processamento"] is None


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
