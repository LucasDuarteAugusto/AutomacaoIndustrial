class ErroDominio(Exception):
    status: int = 400
    titulo: str = "Requisição inválida"
    tipo: str = "about:blank"

    def __init__(self, detalhe: str) -> None:
        super().__init__(detalhe)
        self.detalhe = detalhe


class NaoEncontrado(ErroDominio):
    status = 404
    titulo = "Recurso não encontrado"


class Conflito(ErroDominio):
    status = 409
    titulo = "Conflito"


class RegraNegocio(ErroDominio):
    status = 422
    titulo = "Regra de negócio violada"


class ServicoIndisponivel(ErroDominio):
    status = 503
    titulo = "Serviço indisponível"
