import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RUFF_VERSAO = "0.17.0"


def ler_entrada() -> dict:
    bruto = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    return json.loads(bruto) if bruto.strip() else {}


def responder(**campos: object) -> None:
    sys.stdout.write(json.dumps(campos))
    sys.stdout.flush()
    sys.exit(0)


def raiz_projeto(inicio: Path) -> Path | None:
    for pasta in [inicio, *inicio.parents]:
        if (pasta / "pyproject.toml").is_file():
            return pasta
    return None


def pyproject_cita(raiz: Path, pacote: str) -> bool:
    return pacote in (raiz / "pyproject.toml").read_text(encoding="utf-8", errors="replace")


def comando_ferramenta(raiz: Path, ferramenta: str) -> list[str] | None:
    if not shutil.which("uv"):
        return None
    if pyproject_cita(raiz, ferramenta):
        return ["uv", "run", "--quiet", ferramenta]
    if ferramenta == "ruff":
        return ["uvx", "--quiet", f"ruff@{RUFF_VERSAO}"]
    return None


def rodar(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "FORCE_COLOR"} | {"NO_COLOR": "1"}
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
