from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from supabase import create_client
from app.core.config import settings
from app.presentation.dependencies import get_db
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.application.services.usuario_service import UsuarioService
from app.infrastructure.security import verify_supabase_token, SupabaseTokenData
from app.domain.schemas.usuario import UsuarioCreate, UsuarioResponse, LoginRequest, LoginResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _supabase_admin():
    """Crea cliente Supabase con service_role para operaciones admin."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no está configurado en el servidor",
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Inicia sesión con email y contraseña via Supabase Auth.
    Retorna el JWT de Supabase para usar en el header Authorization.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no está configurado",
        )
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )
        return LoginResponse(
            access_token=response.session.access_token,
            token_type="bearer",
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg or "Email not confirmed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )
        logger.error(f"Error en login: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar sesión",
        )


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registro público. Crea la cuenta en Supabase Auth y el perfil en la BD.
    Solo permite rol 'cliente'.
    """
    usuario_data.rol = "cliente"

    supabase = _supabase_admin()

    # 1. Verificar que el email no exista ya en nuestra BD
    repo = UsuarioRepository(db)
    if repo.get_by_email(usuario_data.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    # 2. Crear usuario en Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": usuario_data.correo,
            "password": usuario_data.password,
            "email_confirm": True,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear cuenta: {str(e)}",
        )

    # 3. Crear perfil en nuestra BD con el mismo UUID de Supabase Auth
    try:
        from uuid import UUID
        usuario_data.id = UUID(str(auth_response.user.id))
        service = UsuarioService(repo)
        return service.create_usuario(usuario_data)
    except HTTPException:
        # Si falla la BD, eliminar el usuario de Supabase Auth para no dejar huérfanos
        try:
            supabase.auth.admin.delete_user(str(auth_response.user.id))
        except Exception:
            pass
        raise



@router.get("/me", response_model=UsuarioResponse)
def me(
    token_data: SupabaseTokenData = Depends(verify_supabase_token),
    db: Session = Depends(get_db),
):
    """Retorna el perfil del usuario autenticado."""
    repo = UsuarioRepository(db)
    user = repo.get_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UsuarioResponse.model_validate(user)


@router.post("/admin/create-user", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    usuario_data: UsuarioCreate,
    token_data: SupabaseTokenData = Depends(verify_supabase_token),
    db: Session = Depends(get_db),
):
    """
    Crea un usuario con cualquier rol. Solo accesible para admins.
    """
    # Verificar que el solicitante es admin
    repo = UsuarioRepository(db)
    admin_user = repo.get_by_id(token_data.user_id)
    if not admin_user or admin_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear usuarios",
        )

    # Validar rol permitido
    if usuario_data.rol not in ("admin", "cliente", "empleada"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol inválido. Debe ser: admin, cliente o empleada",
        )

    # Verificar que el email no exista en BD
    if repo.get_by_email(usuario_data.correo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    supabase = _supabase_admin()

    # Crear usuario en Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": usuario_data.correo,
            "password": usuario_data.password,
            "email_confirm": True,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear cuenta: {str(e)}",
        )

    # Crear perfil en BD con el UUID de Supabase Auth
    try:
        from uuid import UUID
        usuario_data.id = UUID(str(auth_response.user.id))
        service = UsuarioService(repo)
        return service.create_usuario(usuario_data)
    except HTTPException:
        try:
            supabase.auth.admin.delete_user(str(auth_response.user.id))
        except Exception:
            pass
        raise


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    token_data: SupabaseTokenData = Depends(verify_supabase_token),
    db: Session = Depends(get_db),
):
    """
    Cambia la contraseña del usuario autenticado.
    Verifica la contraseña actual via login y luego actualiza via admin API.
    """
    repo = UsuarioRepository(db)
    user = repo.get_by_id(token_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Verificar contraseña actual haciendo login
    try:
        supabase_anon = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        supabase_anon.auth.sign_in_with_password(
            {"email": user.correo, "password": request.current_password}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    # Actualizar contraseña via admin API
    try:
        supabase_admin = _supabase_admin()
        supabase_admin.auth.admin.update_user_by_id(
            str(token_data.user_id),
            {"password": request.new_password},
        )
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la contraseña",
        )

    return {"message": "Contraseña actualizada correctamente"}
