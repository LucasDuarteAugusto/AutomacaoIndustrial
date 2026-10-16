from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from httpx import AsyncClient
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

from app.catalogo.schemas import EquipamentoCreate, FabricanteCreate, FamiliaCreate
from app.documentos.models import Idioma, TipoDocumento
from app.documentos.schemas import DocumentoCreate
from app.falhas.models import TipoFalha
from app.falhas.schemas import FalhaCreate
from app.parametros.schemas import ParametroCreate


def _sufixo() -> str:
    return uuid4().hex[:8].upper()


class FabricanteCreateFactory(ModelFactory[FabricanteCreate]):
    nome = Use(lambda: f"Fabricante {_sufixo()}")
    site = None
    ativo = True


class FamiliaCreateFactory(ModelFactory[FamiliaCreate]):
    nome = Use(lambda: f"Família {_sufixo()}")
    descricao = None
    ativo = True


class EquipamentoCreateFactory(ModelFactory[EquipamentoCreate]):
    codigo_pedido = Use(lambda: f"6SL3210-{_sufixo()}")
    nome = Use(lambda: f"PM240-2 {_sufixo()}")
    potencia_kw = Decimal("5.5")
    tensao_nominal_v = 400
    corrente_nominal_a = Decimal("11.8")
    ativo = True


class DocumentoCreateFactory(ModelFactory[DocumentoCreate]):
    titulo = Use(lambda: f"Manual de parâmetros {_sufixo()}")
    tipo_documento = TipoDocumento.LISTA_PARAMETROS
    idioma = Idioma.PT_BR
    codigo_documento = None
    edicao = "09/2023"
    versao_firmware = "4.7 SP14"
    ids_equipamentos = Use(list[UUID])


async def _post(client: AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = await client.post(url, json=payload)
    assert resp.status_code == 201, resp.text
    corpo: dict[str, Any] = resp.json()
    return corpo


async def id_tipo(client: AsyncClient, codigo: str = "INVERSOR") -> str:
    resp = await client.get("/v1/tipos-equipamento")
    id_tipo_equipamento: str = next(t["id_tipo_equipamento"] for t in resp.json()["items"] if t["codigo"] == codigo)
    return id_tipo_equipamento


async def criar_fabricante(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    payload = FabricanteCreateFactory.build(**campos).model_dump(mode="json")
    return await _post(client, "/v1/fabricantes", payload)


async def criar_familia(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    campos.setdefault("id_fabricante", (await criar_fabricante(client))["id_fabricante"])
    campos.setdefault("id_tipo_equipamento", await id_tipo(client))
    payload = FamiliaCreateFactory.build(**campos).model_dump(mode="json")
    return await _post(client, "/v1/familias", payload)


async def criar_equipamento(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    campos.setdefault("id_familia", (await criar_familia(client))["id_familia"])
    payload = EquipamentoCreateFactory.build(**campos).model_dump(mode="json")
    return await _post(client, "/v1/equipamentos", payload)


async def criar_documento(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    campos.setdefault("ids_familias", [(await criar_familia(client))["id_familia"]])
    payload = DocumentoCreateFactory.build(**campos).model_dump(mode="json")
    return await _post(client, "/v1/documentos", payload)


async def criar_parametro(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    campos.setdefault("id_familia", (await criar_familia(client))["id_familia"])
    campos.setdefault("codigo", f"p{uuid4().hex[:4]}")
    campos.setdefault("descricao", "Parâmetro de teste para comissionamento")
    campos.setdefault("idioma", Idioma.PT_BR)
    payload = ParametroCreate(**campos).model_dump(mode="json")
    return await _post(client, "/v1/parametros", payload)


async def criar_falha(client: AsyncClient, **campos: Any) -> dict[str, Any]:
    campos.setdefault("id_familia", (await criar_familia(client))["id_familia"])
    campos.setdefault("codigo", f"F{uuid4().hex[:5].upper()}")
    campos.setdefault("tipo", TipoFalha.FALHA)
    campos.setdefault("titulo", "Falha de teste")
    campos.setdefault("idioma", Idioma.PT_BR)
    payload = FalhaCreate(**campos).model_dump(mode="json")
    return await _post(client, "/v1/falhas", payload)
