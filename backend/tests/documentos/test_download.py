import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from httpx import AsyncClient

from app.auth.deps import get_usuario_atual, usuario_para_teste
from app.auth.models import Perfil
from app.core.config import Settings
from tests.documentos.test_upload import PDF_MINIMO
from tests.factories import criar_documento


async def _documento_com_pdf(client: AsyncClient, **campos: object) -> dict[str, str]:
    doc = await criar_documento(client, **campos)
    resp = await client.post(
        f"/v1/documentos/{doc['id_documento']}/arquivo",
        files={"arquivo": ("manual.pdf", PDF_MINIMO, "application/pdf")},
    )
    assert resp.status_code == 200, resp.text
    corpo: dict[str, str] = resp.json()
    return corpo


async def test_baixar_arquivo_devolve_pdf_inline(client: AsyncClient) -> None:
    doc = await _documento_com_pdf(client, titulo="Manual de parâmetros G120", codigo_documento=None)

    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo")

    assert resp.status_code == 200
    assert resp.content == PDF_MINIMO
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.headers["etag"] == f'"{hashlib.sha256(PDF_MINIMO).hexdigest()}"'
    assert resp.headers["cache-control"] == "private, max-age=0, must-revalidate"
    disposicao = resp.headers["content-disposition"]
    assert disposicao.startswith('inline; filename="Manual-de-parametros-G120.pdf"')
    assert "filename*=UTF-8''Manual%20de%20par%C3%A2metros%20G120.pdf" in disposicao


async def test_baixar_arquivo_usa_codigo_do_documento_no_nome(client: AsyncClient) -> None:
    doc = await _documento_com_pdf(client, codigo_documento="A5E33840768")
    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo")
    assert 'filename="A5E33840768.pdf"' in resp.headers["content-disposition"]


async def test_baixar_arquivo_com_etag_igual_retorna_304(client: AsyncClient) -> None:
    doc = await _documento_com_pdf(client)
    url = f"/v1/documentos/{doc['id_documento']}/arquivo"
    etag = (await client.get(url)).headers["etag"]

    resp = await client.get(url, headers={"If-None-Match": f'W/"outro", {etag}'})

    assert resp.status_code == 304
    assert resp.content == b""
    assert resp.headers["etag"] == etag


async def test_baixar_arquivo_com_etag_diferente_retorna_200(client: AsyncClient) -> None:
    doc = await _documento_com_pdf(client)
    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo", headers={"If-None-Match": '"antigo"'})
    assert resp.status_code == 200
    assert resp.content == PDF_MINIMO


async def test_baixar_arquivo_de_documento_inexistente_retorna_404(client: AsyncClient) -> None:
    resp = await client.get(f"/v1/documentos/{uuid4()}/arquivo")
    assert resp.status_code == 404
    assert resp.headers["content-type"] == "application/problem+json"


async def test_baixar_arquivo_de_documento_sem_pdf_retorna_404(client: AsyncClient) -> None:
    doc = await criar_documento(client)
    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo")
    assert resp.status_code == 404
    assert "não possui arquivo" in resp.json()["detail"]


async def test_baixar_arquivo_apagado_do_armazenamento_retorna_404(client: AsyncClient, settings: Settings) -> None:
    doc = await _documento_com_pdf(client)
    (Path(settings.armazenamento_caminho) / doc["chave_arquivo"]).unlink()

    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo")

    assert resp.status_code == 404
    assert "armazenamento" in resp.json()["detail"]


async def test_perfil_leitura_pode_baixar_arquivo(client: AsyncClient, app: FastAPI) -> None:
    doc = await _documento_com_pdf(client)
    app.dependency_overrides[get_usuario_atual] = lambda: usuario_para_teste(Perfil.LEITURA)

    resp = await client.get(f"/v1/documentos/{doc['id_documento']}/arquivo")

    assert resp.status_code == 200
    assert resp.content == PDF_MINIMO
