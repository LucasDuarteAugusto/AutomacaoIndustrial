from uuid import UUID

from fastapi import BackgroundTasks, Request

from app.ingestao.pipeline import processar_documento_em_background


def agendar_ingestao(background: BackgroundTasks, request: Request, id_documento: UUID) -> None:
    app = request.app
    background.add_task(
        processar_documento_em_background,
        app.state.sessionmaker,
        armazenamento=app.state.armazenamento,
        embedding=app.state.provedor_embedding,
        settings=app.state.settings,
        id_documento=id_documento,
    )
