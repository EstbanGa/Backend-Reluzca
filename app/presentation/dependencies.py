"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.security import decode_token
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.models.usuario import Usuario

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Usuario: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user_id from token
    user_id: str = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    usuario_repo = UsuarioRepository(db)
    user = usuario_repo.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Check if user is active
    if user.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    return user


async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Get current active user.
    Alias for get_current_user for clarity.
    """
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific user role.
    
    Args:
        required_role: Required role (admin, cliente, empleada)
        
    Returns:
        Dependency function that checks user role
        
    Usage:
        @app.get("/admin/dashboard")
        async def admin_dashboard(
            current_user: Usuario = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {required_role}"
            )
        return current_user
    
    return role_checker


# Specific role dependencies
async def require_admin(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Require admin role."""
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador"
        )
    return current_user


async def require_cliente(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Require cliente role."""
    if current_user.rol != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo para clientes"
        )
    return current_user


async def require_empleada(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Require empleada role."""
    if current_user.rol != "empleada":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo para empleadas"
        )
    return current_user


async def require_admin_or_empleada(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Require admin or empleada role."""
    if current_user.rol not in ["admin", "empleada"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo para administradores o empleadas"
        )
    return current_user


# Optional authentication
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
        
    Returns:
        Optional[Usuario]: Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            return None
        
        user_id: str = payload.get("user_id")
        if not user_id:
            return None
        
        usuario_repo = UsuarioRepository(db)
        user = usuario_repo.get_by_id(user_id)
        
        if user and user.estado == "activo":
            return user
        
        return None
    except:
        return None
