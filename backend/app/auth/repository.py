from sqlalchemy import ColumnElement, func, or_, select

from app.auth.models import Perfil, Usuario
from app.core.repository import RepositorioBase


class UsuarioRepository(RepositorioBase[Usuario]):
    modelo = Usuario

    async def obter_por_email(self, email: str) -> Usuario | None:
        return await self.session.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    async def contar(self) -> int:
        total = await self.session.scalar(select(func.count()).select_from(Usuario))
        return int(total or 0)

    async def contar_admins_ativos(self) -> int:
        total = await self.session.scalar(
            select(func.count()).select_from(Usuario).where(Usuario.perfil == Perfil.ADMIN, Usuario.ativo.is_(True))
        )
        return int(total or 0)

    async def listar(
        self,
        busca: str | None,
        perfil: Perfil | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Usuario], int]:
        filtros: list[ColumnElement[bool]] = []
        if busca:
            filtros.append(
                or_(
                    Usuario.nome.icontains(busca, autoescape=True),
                    Usuario.email.icontains(busca, autoescape=True),
                )
            )
        if perfil:
            filtros.append(Usuario.perfil == perfil)
        if ativo is not None:
            filtros.append(Usuario.ativo.is_(ativo))
        return await self.paginar(filtros, [Usuario.nome, Usuario.id_usuario], limit, offset)
