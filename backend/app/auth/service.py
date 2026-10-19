from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Perfil, Usuario
from app.auth.repository import UsuarioRepository
from app.auth.schemas import BootstrapRequest, LoginRequest, TokenOut, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.auth.seguranca import criar_access_token, hash_senha, verificar_senha
from app.core.config import Settings
from app.core.errors import Conflito, NaoAutorizado, NaoEncontrado, Proibido
from app.core.schemas import Pagina
from app.core.servicos import aplicar_alteracoes


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.usuarios = UsuarioRepository(session)

    async def login(self, dados: LoginRequest) -> TokenOut:
        usuario = await self.usuarios.obter_por_email(str(dados.email))
        if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
            raise NaoAutorizado("E-mail ou senha inválidos.")
        if not usuario.ativo:
            raise Proibido("Usuário inativo.")
        return self._token_out(usuario)

    async def bootstrap(self, dados: BootstrapRequest) -> TokenOut:
        if await self.usuarios.contar() > 0:
            raise Conflito("Bootstrap indisponível: já existem usuários cadastrados.")
        usuario = Usuario(
            email=str(dados.email).lower(),
            senha_hash=hash_senha(dados.senha),
            nome=dados.nome,
            perfil=Perfil.ADMIN,
            ativo=True,
        )
        await self.usuarios.adicionar(usuario)
        await self.session.commit()
        return self._token_out(usuario)

    async def criar_usuario(self, dados: UsuarioCreate, ator: Usuario) -> UsuarioOut:
        if ator.perfil != Perfil.ADMIN:
            raise Proibido("Apenas ADMIN pode criar usuários.")
        email = str(dados.email).lower()
        if await self.usuarios.obter_por_email(email) is not None:
            raise Conflito(f"Já existe usuário com e-mail {email}.")
        usuario = Usuario(
            email=email,
            senha_hash=hash_senha(dados.senha),
            nome=dados.nome,
            perfil=dados.perfil,
            ativo=dados.ativo,
        )
        await self.usuarios.adicionar(usuario)
        await self.session.commit()
        return UsuarioOut.model_validate(usuario)

    async def alterar_usuario(self, id_usuario: UUID, dados: UsuarioUpdate, ator: Usuario) -> UsuarioOut:
        if ator.perfil != Perfil.ADMIN:
            raise Proibido("Apenas ADMIN pode alterar usuários.")
        usuario = await self._obter(id_usuario)
        await self._garantir_admin_restante(usuario, dados)
        if dados.senha is not None:
            usuario.senha_hash = hash_senha(dados.senha)
        aplicar_alteracoes(usuario, dados, ignorar={"senha"})
        await self.session.commit()
        return UsuarioOut.model_validate(usuario)

    async def listar_usuarios(
        self,
        busca: str | None,
        perfil: Perfil | None,
        ativo: bool | None,
        limit: int,
        offset: int,
    ) -> Pagina[UsuarioOut]:
        itens, total = await self.usuarios.listar(busca, perfil, ativo, limit, offset)
        return Pagina(items=[UsuarioOut.model_validate(u) for u in itens], total=total)

    async def obter_usuario_admin(self, id_usuario: UUID) -> UsuarioOut:
        return UsuarioOut.model_validate(await self._obter(id_usuario))

    async def _obter(self, id_usuario: UUID) -> Usuario:
        usuario = await self.usuarios.obter(id_usuario)
        if usuario is None:
            raise NaoEncontrado(f"Usuário {id_usuario} não encontrado.")
        return usuario

    async def _garantir_admin_restante(self, usuario: Usuario, dados: UsuarioUpdate) -> None:
        if usuario.perfil != Perfil.ADMIN or not usuario.ativo:
            return
        rebaixa = dados.perfil is not None and dados.perfil != Perfil.ADMIN
        desativa = dados.ativo is False
        if (rebaixa or desativa) and await self.usuarios.contar_admins_ativos() <= 1:
            raise Conflito("Não é possível rebaixar ou desativar o último ADMIN ativo.")

    async def obter_usuario(self, id_usuario: UUID) -> Usuario:
        usuario = await self.usuarios.obter(id_usuario)
        if usuario is None or not usuario.ativo:
            raise NaoAutorizado("Usuário inválido ou inativo.")
        return usuario

    def _token_out(self, usuario: Usuario) -> TokenOut:
        token = criar_access_token(
            settings=self.settings,
            id_usuario=usuario.id_usuario,
            email=usuario.email,
            perfil=usuario.perfil,
        )
        return TokenOut(
            access_token=token,
            expires_in=self.settings.jwt_expiracao_minutos * 60,
            usuario=UsuarioOut.model_validate(usuario),
        )


def exigir_escrita(usuario: Usuario) -> None:
    if usuario.perfil == Perfil.LEITURA:
        raise Proibido("Perfil LEITURA não pode alterar dados.")
