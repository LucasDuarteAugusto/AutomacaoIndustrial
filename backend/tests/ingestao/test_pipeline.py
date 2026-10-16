from uuid import UUID

import fitz
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.trechos.models import Trecho
from tests.factories import criar_documento


def _pdf_com_texto(texto: str) -> bytes:
    documento = fitz.open()
    try:
        pagina = documento.new_page()
        pagina.insert_text((72, 72), texto)
        return bytes(documento.tobytes())
    finally:
        documento.close()


async def test_upload_indexa_trechos(client: AsyncClient, db_session: AsyncSession) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    pdf = _pdf_com_texto("Parâmetro p1120 — tempo de rampa de aceleração: 10 s.")

    resp = await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("g120.pdf", pdf, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["status_processamento"] == "INDEXADO"
    assert corpo["paginas"] == 1
    assert corpo["erro_processamento"] is None

    total = await db_session.scalar(select(func.count()).select_from(Trecho).where(Trecho.id_documento == UUID(id_doc)))
    assert total is not None and total >= 1

    com_busca = await db_session.scalar(
        text('SELECT count(*) FROM "TRECHOS" WHERE "ID_DOCUMENTO" = :id AND "CONTEUDO_BUSCA" IS NOT NULL'),
        {"id": id_doc},
    )
    assert com_busca == total

    com_embedding = await db_session.scalar(
        text('SELECT count(*) FROM "TRECHOS" WHERE "ID_DOCUMENTO" = :id AND "EMBEDDING" IS NOT NULL'),
        {"id": id_doc},
    )
    assert com_embedding == total


async def test_reprocessar_documento_indexado(client: AsyncClient, db_session: AsyncSession) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    pdf = _pdf_com_texto("Código de falha F07801: sobrecorrente no inversor.")
    await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("falhas.pdf", pdf, "application/pdf")},
    )
    assert (await client.get(f"/v1/documentos/{id_doc}")).json()["status_processamento"] == "INDEXADO"

    resp = await client.post(f"/v1/documentos/{id_doc}/reprocessar")
    assert resp.status_code == 200
    assert resp.json()["status_processamento"] == "INDEXADO"

    total = await db_session.scalar(select(func.count()).select_from(Trecho).where(Trecho.id_documento == UUID(id_doc)))
    assert total is not None and total >= 1


async def test_pdf_sem_texto_marca_erro(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    id_doc = doc["id_documento"]
    documento = fitz.open()
    try:
        documento.new_page()
        pdf_vazio = bytes(documento.tobytes())
    finally:
        documento.close()

    resp = await client.post(
        f"/v1/documentos/{id_doc}/arquivo",
        files={"arquivo": ("vazio.pdf", pdf_vazio, "application/pdf")},
    )
    assert resp.status_code == 422
    detalhe = resp.json()["detail"]
    assert "texto" in detalhe.lower() or "extraível" in detalhe.lower()

    status = (await client.get(f"/v1/documentos/{id_doc}")).json()
    assert status["status_processamento"] == "ERRO"
    assert status["erro_processamento"]
