"""
Security utilities for authentication using Supabase Auth.

Strategy:
  1. Si SUPABASE_JWT_SECRET está configurado → verificación local HS256 (no consulta
     Supabase, resistente a invalidación de sesión por cambio de contraseña).
  2. Si no → fallback a get_user() contra la API de Supabase.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class SupabaseTokenData(BaseModel):
    """Datos extraidos del JWT de Supabase."""
    user_id: UUID
    email: Optional[str] = None
    exp: datetime


def _verify_local(token: str) -> SupabaseTokenData:
    """Verificación local HS256 con SUPABASE_JWT_SECRET."""
    payload = pyjwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience=settings.SUPABASE_JWT_AUDIENCE,
        options={"require": ["sub", "exp"]},
    )
    return SupabaseTokenData(
        user_id=UUID(str(payload["sub"])),
        email=payload.get("email"),
        exp=datetime.fromtimestamp(payload["exp"]),
    )


def _verify_remote(token: str) -> SupabaseTokenData:
    """Verificación remota vía Supabase Admin SDK (get_user)."""
    from supabase import create_client
    sup = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    response = sup.auth.get_user(token)
    if not response.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    unverified = pyjwt.decode(token, options={"verify_signature": False})
    return SupabaseTokenData(
        user_id=UUID(str(response.user.id)),
        email=response.user.email,
        exp=datetime.fromtimestamp(unverified.get("exp", 0)),
    )


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SupabaseTokenData:
    """
    Valida el JWT de Supabase.
    - Con SUPABASE_JWT_SECRET: verificación local (recomendado).
    - Sin él: delega a get_user() de Supabase (requiere sesión activa).
    """
    token = credentials.credentials

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no está configurado en el servidor",
        )

    try:
        if settings.SUPABASE_JWT_SECRET:
            return _verify_local(token)
        return _verify_remote(token)

    except HTTPException:
        raise
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Inicia sesión nuevamente.",
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido. Inicia sesión nuevamente.",
        )
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Error al validar token: {error_msg}")
        # Sesión invalidada por cambio de contraseña u otro motivo
        if "session" in error_msg.lower() and "does not exist" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión expirada. Por favor, inicia sesión nuevamente.",
            )
        if any(k in error_msg.lower() for k in ["invalid", "expired", "jwt", "unauthorized"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado. Inicia sesión nuevamente.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {error_msg}",
        )

