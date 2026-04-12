"""
FastAPI dependencies for authentication and authorization.
Uses Supabase Auth JWT validation via JWKS.
"""
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.security import verify_supabase_token, SupabaseTokenData
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.models.usuario import Usuario


async def get_current_user(
    token_data: SupabaseTokenData = Depends(verify_supabase_token),
    db: Session = Depends(get_db),
) -> Usuario:
    repo = UsuarioRepository(db)
    user = repo.get_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    if user.estado != "activo":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    return user


async def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    return current_user


def require_role(required_role: str):
    async def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {required_role}",
            )
        return current_user
    return role_checker


async def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return current_user


async def require_cliente(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "cliente":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo clientes")
    return current_user


async def require_empleada(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol != "empleada":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo empleadas")
    return current_user


async def require_admin_or_empleada(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol not in ["admin", "empleada"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores o empleadas")
    return current_user
