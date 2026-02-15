from datetime import datetime, timedelta
from typing import Optional
import logging
from jose import JWTError, jwt
from app.core.config import settings
from app.core.security import verify_password, hash_password
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioLogin, Token, TokenData, UsuarioResponse
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def authenticate_user(self, login_data: UsuarioLogin) -> Optional[Usuario]:
        """Autentica un usuario verificando email y contraseña"""
        user = self.usuario_repository.get_by_email(login_data.correo)
        if not user:
            return None
        if not verify_password(login_data.password, user.password):
            return None
        if user.estado != "activo":  # Solo usuarios con estado "activo" pueden iniciar sesión
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def login(self, login_data: UsuarioLogin) -> Optional[Token]:
        """Procesa el login y retorna el token"""
        user = self.authenticate_user(login_data)
        if not user:
            return None

        logger.info(f"✅ Usuario autenticado: {user.nombre} {user.apellido} ({user.correo})")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.correo, "rol": user.rol},
            expires_delta=access_token_expires
        )
        
        # Convertir usuario a dict y mapear correo -> email
        user_dict = {
            "id": user.id,
            "rol": user.rol,
            "fecha_registro": user.fecha_registro,
            "nombre": user.nombre,
            "apellido": user.apellido,
            "email": user.correo,  # Mapear correo a email
            "documento": user.documento,
            "telefono": user.telefono,
            "tipo_persona": user.tipo_persona,
            "fecha_nacimiento": user.fecha_nacimiento,
            "estado": user.estado,
            "ranking": user.ranking,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }

        logger.info(f"📤 Token generado. User data: {user_dict}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UsuarioResponse(**user_dict)
        )

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
