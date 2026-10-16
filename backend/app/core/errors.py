class ErroDominio(Exception):
    status: int = 400
    titulo: str = "Requisição inválida"
    tipo: str = "about:blank"

    def __init__(self, detalhe: str) -> None:
        super().__init__(detalhe)
        self.detalhe = detalhe


class NaoAutorizado(ErroDominio):
    status = 401
    titulo = "Não autorizado"


class Proibido(ErroDominio):
    status = 403
    titulo = "Proibido"


class NaoEncontrado(ErroDominio):
    status = 404
    titulo = "Recurso não encontrado"


class Conflito(ErroDominio):
    status = 409
    titulo = "Conflito"


class RegraNegocio(ErroDominio):
    status = 422
    titulo = "Regra de negócio violada"


class LimiteExcedido(ErroDominio):
    status = 429
    titulo = "Limite de requisições excedido"

    def __init__(self, detalhe: str, *, retry_after: int = 60) -> None:
        super().__init__(detalhe)
        self.retry_after = retry_after


class ServicoIndisponivel(ErroDominio):
    status = 503
    titulo = "Serviço indisponível"
