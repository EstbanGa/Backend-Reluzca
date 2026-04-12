"""
AuthService — La autenticación ahora la gestiona Supabase Auth vía los endpoints /auth/login y /auth/register.
Este módulo se mantiene como stub de compatibilidad para no romper las importaciones existentes.
"""
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class AuthService:
    """Stub de compatibilidad. La auth real la hace Supabase."""

    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            correo: str = payload.get("sub")
            rol: str = payload.get("rol")
            if correo is None:
                return None
            return TokenData(correo=correo, rol=rol)
        except JWTError:
            return None

    def get_current_user(self, token: str) -> Optional[Usuario]:
        """Obtiene el usuario actual a partir del token"""
        token_data = self.verify_token(token)
        if token_data is None:
            return None
        
        user = self.usuario_repository.get_by_email(token_data.correo)
        if user is None:
            return None
        
        return user
