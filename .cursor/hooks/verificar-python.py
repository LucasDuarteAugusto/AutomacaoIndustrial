import subprocess
from pathlib import Path

from _comum import comando_ferramenta, ler_entrada, pyproject_cita, responder, rodar

LINHAS_POR_FALHA = 60


def houve_mudanca_python(raiz: Path) -> bool:
    try:
        saida = rodar(["git", "status", "--porcelain", "--untracked-files=all"], raiz, 10)
    except (OSError, subprocess.SubprocessError):
        return True
    if saida.returncode != 0:
        return True
    return any(linha.rstrip().endswith((".py", ".pyi", "pyproject.toml")) for linha in saida.stdout.splitlines())


def verificacoes(raiz: Path) -> list[tuple[str, list[str], int]]:
    lista: list[tuple[str, list[str], int]] = []
    ruff = comando_ferramenta(raiz, "ruff")
    if ruff:
        lista.append(("ruff check", [*ruff, "check", "--output-format=concise", "."], 120))
    if pyproject_cita(raiz, "mypy"):
        alvo = "app" if (raiz / "app").is_dir() else "."
        lista.append(("mypy", ["uv", "run", "--quiet", "mypy", alvo], 300))
    if pyproject_cita(raiz, "pytest") and (raiz / "tests").is_dir():
        lista.append(("pytest", ["uv", "run", "--quiet", "pytest", "-x", "-q", "--lf", "--no-header"], 480))
    return lista


def projetos_python(raiz: Path) -> list[Path]:
    if (raiz / "pyproject.toml").is_file():
        return [raiz]
    return sorted(p for p in raiz.iterdir() if p.is_dir() and (p / "pyproject.toml").is_file())


def main() -> None:
    entrada = ler_entrada()
    raiz = Path.cwd()
    projetos = projetos_python(raiz)
    if entrada.get("status") != "completed" or not projetos:
        responder()
    if not houve_mudanca_python(raiz):
        responder()

    falhas: list[str] = []
    for projeto in projetos:
        prefixo = "" if projeto == raiz else f"{projeto.name}: "
        for nome, cmd, timeout in verificacoes(projeto):
            try:
                resultado = rodar(cmd, projeto, timeout)
            except subprocess.TimeoutExpired:
                falhas.append(f"### {prefixo}{nome}\nTempo esgotado ({timeout}s).")
                continue
            except OSError as erro:
                falhas.append(f"### {prefixo}{nome}\nNão foi possível executar: {erro}")
                continue
            if resultado.returncode not in (0, 5):
                saida = (resultado.stdout + resultado.stderr).strip().splitlines()
                falhas.append(f"### {prefixo}{nome}\n" + "\n".join(saida[-LINHAS_POR_FALHA:]))

    if not falhas:
        responder()
    responder(
        followup_message=(
            "As verificações automáticas falharam após suas alterações. Corrija os problemas abaixo "
            "(sem desabilitar regras nem pular testes) e rode novamente:\n\n" + "\n\n".join(falhas)
        )
    )


if __name__ == "__main__":
    main()
