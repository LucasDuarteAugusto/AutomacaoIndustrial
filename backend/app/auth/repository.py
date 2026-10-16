from sqlalchemy import func, select

from app.auth.models import Usuario
from app.core.repository import RepositorioBase


class UsuarioRepository(RepositorioBase[Usuario]):
    modelo = Usuario

    async def obter_por_email(self, email: str) -> Usuario | None:
        return await self.session.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    async def contar(self) -> int:
        total = await self.session.scalar(select(func.count()).select_from(Usuario))
        return int(total or 0)
