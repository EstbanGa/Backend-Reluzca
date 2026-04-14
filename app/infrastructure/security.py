"""
Security utilities for authentication using Supabase Auth.

Token validation is delegated to the Supabase Admin SDK (get_user call),
which avoids JWKS/HS256 compatibility issues.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class SupabaseTokenData(BaseModel):
    """Datos extraidos del JWT de Supabase."""
    user_id: UUID
    email: Optional[str] = None
    exp: datetime


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SupabaseTokenData:
    """
    Valida el JWT de Supabase delegando la verificación al Admin SDK.
    Funciona con HS256 (default) y RS256 sin configuración extra.
    """
    token = credentials.credentials

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no está configurado en el servidor",
        )

    try:
        sup = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        response = sup.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        # Extraer exp del token sin re-verificar firma (ya lo verificó Supabase)
        unverified = pyjwt.decode(token, options={"verify_signature": False})

        return SupabaseTokenData(
            user_id=UUID(str(response.user.id)),
            email=response.user.email,
            exp=datetime.fromtimestamp(unverified.get("exp", 0)),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Error al validar token: {error_msg}")
        if any(k in error_msg.lower() for k in ["invalid", "expired", "jwt", "unauthorized"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado. Inicia sesión nuevamente.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al validar token: {error_msg}",
        )

