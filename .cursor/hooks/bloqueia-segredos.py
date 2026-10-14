import re
from pathlib import PurePath

from _comum import ler_entrada, responder

PERMITIDOS = re.compile(r"\.env\.(example|sample|template)$", re.I)
SEGREDOS = re.compile(
    r"(^\.env(\..+)?$|\.(pem|key|p12|pfx|jks)$|^id_(rsa|ed25519|ecdsa)$|^credentials\.json$|^secrets?\.(json|ya?ml|toml)$)",
    re.I,
)


def main() -> None:
    entrada = ler_entrada()
    nome = PurePath(entrada.get("file_path") or "").name
    if nome and not PERMITIDOS.search(nome) and SEGREDOS.search(nome):
        responder(permission="deny")
    responder(permission="allow")


if __name__ == "__main__":
    main()
