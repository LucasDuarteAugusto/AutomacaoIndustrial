from uuid import UUID


def chave_documento(id_documento: UUID, hash_sha256: str, *, extensao: str = "pdf") -> str:
    """Chave estável e portátil entre local, R2 e S3: `{id}/{hash}.{ext}`."""
    hash_limpo = hash_sha256.strip().lower()
    if len(hash_limpo) != 64 or any(c not in "0123456789abcdef" for c in hash_limpo):
        msg = "hash_sha256 deve ter 64 caracteres hexadecimais"
        raise ValueError(msg)
    ext = extensao.lstrip(".").lower() or "pdf"
    return f"{id_documento}/{hash_limpo}.{ext}"
