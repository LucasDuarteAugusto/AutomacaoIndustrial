import httpx


def espera_para_retry(resposta: httpx.Response, tentativa: int, base: float, *, teto: float = 120.0) -> float:
    """Segundos de espera antes da próxima tentativa (`Retry-After` tem prioridade)."""
    cabecalho = resposta.headers.get("Retry-After")
    if cabecalho:
        try:
            return max(0.0, float(cabecalho))
        except ValueError:
            pass
    return min(base * 2 ** (tentativa - 1), teto)
