"""Ponto único de importação dos models para o autogenerate do Alembic enxergar todas as tabelas."""

from app.core.db import Base

__all__ = ["Base"]
