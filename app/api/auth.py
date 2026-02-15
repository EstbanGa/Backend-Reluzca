from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.auth import oauth2_scheme
from app.core.dependencies import get_db
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.usuario_service import UsuarioService
from app.schemas.usuario import UsuarioLogin, Token, UsuarioCreate, UsuarioResponse, UsuarioCompleteResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Inyección de dependencias para AuthService"""
    usuario_repository = UsuarioRepository(db)
    return AuthService(usuario_repository)


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """Registra un nuevo usuario"""
    try:
        from app.services.usuario_service import UsuarioService
        usuario_repository = UsuarioRepository(db)
        usuario_service = UsuarioService(usuario_repository)
        return usuario_service.create_usuario(usuario_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Inicia sesión y devuelve un token JWT"""
    login_data = UsuarioLogin(email=form_data.username, password=form_data.password)
    token = auth_service.login(login_data)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post("/login/json", response_model=Token)
def login_json(
    login_data: UsuarioLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Inicia sesión con JSON y devuelve un token JWT"""
    token = auth_service.login(login_data)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.get("/me", response_model=UsuarioResponse)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Obtiene el usuario actual basado en el token"""
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convertir el modelo Usuario a dict y mapear correo -> email
    user_dict = {
        "id": str(user.id),  # Convertir UUID a string
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
    
    response = UsuarioResponse(**user_dict)
    
    return response


@router.get("/me/complete", response_model=UsuarioCompleteResponse)
def get_current_user_complete(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    """
    Obtiene TODA la información del usuario actual:
    - Perfil completo
    - Todas las reservas (como cliente y como empleada)
    - Todas las ubicaciones
    - Información relacionada
    
    Este endpoint está diseñado para cargar toda la información al inicio
    y guardarla en caché en el frontend para evitar múltiples peticiones.
    """
    user = auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario_repository = UsuarioRepository(db)
    usuario_service = UsuarioService(usuario_repository)
    return usuario_service.get_usuario_complete_info(user.id)
