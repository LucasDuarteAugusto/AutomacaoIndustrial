"""Ponto único de importação dos models para o autogenerate do Alembic enxergar todas as tabelas."""

from app.auth.models import Usuario
from app.catalogo.models import Equipamento, Fabricante, Familia, TipoEquipamento
from app.core.db import Base
from app.documentos.models import Documento, DocumentoEquipamento, DocumentoFamilia
from app.falhas.models import Falha
from app.parametros.models import Parametro
from app.trechos.models import Trecho

__all__ = [
    "Base",
    "Documento",
    "DocumentoEquipamento",
    "DocumentoFamilia",
    "Equipamento",
    "Fabricante",
    "Falha",
    "Familia",
    "Parametro",
    "TipoEquipamento",
    "Trecho",
    "Usuario",
]
