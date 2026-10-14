"""Ponto único de importação dos models para o autogenerate do Alembic enxergar todas as tabelas."""

from app.catalogo.models import Equipamento, Fabricante, Familia, TipoEquipamento
from app.core.db import Base
from app.documentos.models import Documento, DocumentoEquipamento, DocumentoFamilia

__all__ = [
    "Base",
    "Documento",
    "DocumentoEquipamento",
    "DocumentoFamilia",
    "Equipamento",
    "Fabricante",
    "Familia",
    "TipoEquipamento",
]
