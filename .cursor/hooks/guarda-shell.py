import re
import subprocess
from pathlib import Path

from _comum import ler_entrada, responder

PROTEGIDAS = {"development", "master", "main"}

PIP_INSTALL = re.compile(r"(^|\s)((py|python[\d.]*)\s+(-\d[\d.]*\s+)?-m\s+)?(uv\s+)?pip3?\s+install\b", re.I)
ALEMBIC_DOWNGRADE = re.compile(r"\balembic\b.*\bdowngrade\b", re.I)
SQL_DESTRUTIVO = re.compile(r"\b(drop\s+(table|database|schema)|truncate\s+(table\s+)?\w)", re.I)
SEPARADORES = re.compile(r"&&|\|\||;|\|")


def branch_atual(cwd: str | None) -> str:
    try:
        saida = subprocess.run(
            ["git", "branch", "--show-current"], cwd=cwd, capture_output=True, text=True, timeout=5
        )
        return saida.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def destino_push(tokens: list[str], cwd: str | None) -> str:
    posicionais = [t for t in tokens if not t.startswith("-")]
    refspecs = posicionais[1:]
    if not refspecs:
        return branch_atual(cwd)
    destino = refspecs[-1].lstrip("+").split(":")[-1]
    destino = destino.removeprefix("refs/heads/")
    return branch_atual(cwd) if destino == "HEAD" else destino


def avaliar(segmento: str, cwd: str | None) -> tuple[str, str] | None:
    if PIP_INSTALL.search(segmento):
        return "deny", "Use `uv add <pacote>` (ou `uv add --dev <pacote>`) em vez de pip install; a rule stack-versions exige dependências via uv."

    if ALEMBIC_DOWNGRADE.search(segmento):
        return "ask", "alembic downgrade remove estrutura do banco. Confirme que DATABASE_URL aponta para o banco local."

    if SQL_DESTRUTIVO.search(segmento):
        return "ask", "Comando com DROP/TRUNCATE detectado. Confirme o banco de destino antes de executar."

    tokens = segmento.split()
    if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "push":
        if any(t in ("-f", "--force") or t.startswith("--force") for t in tokens):
            return "ask", "git push com --force reescreve histórico remoto. Confirme."
        destino = destino_push(tokens[2:], cwd)
        if destino in PROTEGIDAS:
            return "deny", f"Push direto para `{destino}` é proibido (rule protected-branches). Use uma branch feat/ ou fix/ e abra PR."

    if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "commit":
        atual = branch_atual(cwd)
        if atual in PROTEGIDAS:
            return "ask", f"Commit na branch protegida `{atual}`. Só prossiga se o usuário pediu explicitamente."

    return None


def main() -> None:
    entrada = ler_entrada()
    comando = entrada.get("command") or ""
    cwd = entrada.get("cwd") or None
    if cwd and not Path(cwd).is_dir():
        cwd = None

    peso = {"deny": 2, "ask": 1}
    decisao: tuple[str, str] | None = None
    for segmento in SEPARADORES.split(comando):
        resultado = avaliar(segmento.strip(), cwd)
        if resultado and (decisao is None or peso[resultado[0]] > peso[decisao[0]]):
            decisao = resultado

    if decisao is None:
        responder(permission="allow")
    permissao, mensagem = decisao
    responder(permission=permissao, user_message=mensagem, agent_message=mensagem)


if __name__ == "__main__":
    main()
