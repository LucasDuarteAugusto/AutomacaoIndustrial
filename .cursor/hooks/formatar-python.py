import subprocess
from pathlib import Path

from _comum import comando_ferramenta, ler_entrada, raiz_projeto, responder, rodar


def main() -> None:
    entrada = ler_entrada()
    arquivo = Path(entrada.get("file_path") or "")
    if arquivo.suffix not in (".py", ".pyi") or not arquivo.is_file():
        responder()

    raiz = raiz_projeto(arquivo.resolve().parent)
    ruff = comando_ferramenta(raiz, "ruff") if raiz else None
    if not ruff:
        responder()

    try:
        rodar([*ruff, "check", "--fix", "--exit-zero", str(arquivo)], raiz, 45)
        rodar([*ruff, "format", str(arquivo)], raiz, 45)
    except (OSError, subprocess.SubprocessError):
        pass
    responder()


if __name__ == "__main__":
    main()
