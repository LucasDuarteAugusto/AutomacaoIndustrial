from uuid import uuid4

import pytest

from app.auth.models import Perfil
from app.auth.seguranca import criar_access_token, decodificar_access_token, hash_senha, verificar_senha
from app.core.config import Settings
from app.core.errors import NaoAutorizado


def test_hash_e_verificacao_de_senha() -> None:
    digest = hash_senha("minha-senha")
    assert verificar_senha("minha-senha", digest)
    assert not verificar_senha("outra", digest)


def test_token_jwt_roundtrip(settings: Settings) -> None:
    id_usuario = uuid4()
    token = criar_access_token(
        settings=settings,
        id_usuario=id_usuario,
        email="a@b.c",
        perfil=Perfil.OPERADOR,
    )
    payload = decodificar_access_token(token, settings)
    assert payload["sub"] == str(id_usuario)
    assert payload["perfil"] == "OPERADOR"


def test_token_invalido_levanta_nao_autorizado(settings: Settings) -> None:
    with pytest.raises(NaoAutorizado):
        decodificar_access_token("nao.e.um.jwt", settings)
