from pathlib import Path
from uuid import uuid4

import pytest

from app.armazenamento.chave import chave_documento
from app.armazenamento.factory import criar_armazenamento
from app.armazenamento.local import ArmazenamentoLocal
from app.core.config import Settings
from app.core.errors import RegraNegocio


def test_chave_documento_formato_estavel() -> None:
    id_doc = uuid4()
    hash_hex = "a" * 64
    assert chave_documento(id_doc, hash_hex) == f"{id_doc}/{hash_hex}.pdf"
    assert chave_documento(id_doc, hash_hex.upper(), extensao=".PDF") == f"{id_doc}/{hash_hex}.pdf"


def test_chave_documento_hash_invalido() -> None:
    with pytest.raises(ValueError, match="64 caracteres"):
        chave_documento(uuid4(), "abc")


@pytest.mark.asyncio
async def test_local_salvar_carregar_existe_apagar(tmp_path: Path) -> None:
    store = ArmazenamentoLocal(tmp_path)
    chave = chave_documento(uuid4(), "b" * 64)
    conteudo = b"%PDF-1.4 teste"

    assert await store.existe(chave) is False
    await store.salvar(chave, conteudo, content_type="application/pdf")
    assert await store.existe(chave) is True
    assert await store.carregar(chave) == conteudo
    assert (tmp_path / chave).is_file()

    await store.apagar(chave)
    assert await store.existe(chave) is False
    with pytest.raises(FileNotFoundError):
        await store.carregar(chave)


@pytest.mark.asyncio
async def test_local_rejeita_path_traversal(tmp_path: Path) -> None:
    store = ArmazenamentoLocal(tmp_path)
    with pytest.raises(RegraNegocio, match="inválida"):
        await store.salvar("../segredo.pdf", b"x")


def test_factory_cria_local(tmp_path: Path) -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://u:p@localhost:5433/db",
        ambiente="teste",
        armazenamento_tipo="local",
        armazenamento_caminho=str(tmp_path),
    )
    store = criar_armazenamento(settings)
    assert isinstance(store, ArmazenamentoLocal)
    assert store.raiz == tmp_path.resolve()
