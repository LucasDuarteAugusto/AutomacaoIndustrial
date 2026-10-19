"""Exporta o contrato OpenAPI sem banco: `uv run python -m app.core.openapi --saida ../frontend/openapi.json`."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.main import create_app

# O engine só é criado no lifespan; a URL nunca é conectada.
_DATABASE_URL_FICTICIA = "postgresql+asyncpg://openapi:openapi@localhost:5432/openapi"


def gerar_openapi() -> dict[str, Any]:
    settings = Settings(database_url=_DATABASE_URL_FICTICIA, ambiente="teste", rate_limit_habilitado=False)
    return create_app(settings).openapi()


def serializar_openapi(esquema: dict[str, Any]) -> str:
    return json.dumps(esquema, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Exporta o contrato OpenAPI da API.")
    parser.add_argument("--saida", type=Path, help="Arquivo de destino; sem ele, escreve no stdout.")
    args = parser.parse_args(argv)
    conteudo = serializar_openapi(gerar_openapi())
    if args.saida is None:
        sys.stdout.write(conteudo)
        return
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(conteudo, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
