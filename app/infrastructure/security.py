"""
Security utilities for authentication using Supabase Auth + JWKS validation.

The password is managed exclusively by Supabase Auth.
This module validates the JWT tokens Supabase emits.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient
from pydantic import BaseModel
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

_jwks_client: Optional[PyJWKClient] = None


class SupabaseTokenData(BaseModel):
    """Datos extraidos del JWT de Supabase."""
    user_id: UUID
    email: Optional[str] = None
    exp: datetime


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL no esta configurado")
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SupabaseTokenData:
    """Valida el JWT de Supabase usando JWKS y retorna los datos del usuario."""
    token = credentials.credentials

    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase no esta configurado",
        )

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header.get("alg", "RS256")

        supported = ["RS256", "ES256", "HS256"]
        if algorithm not in supported:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Algoritmo '{algorithm}' no soportado",
            )

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=settings.supabase_jwt_issuer,
        )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: falta 'sub'",
            )

        return SupabaseTokenData(
            user_id=UUID(user_id_str),
            email=payload.get("email"),
            exp=datetime.fromtimestamp(payload.get("exp", 0)),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Inicia sesion nuevamente.",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalido: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al procesar token: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo conectar con Supabase JWKS. Verifica SUPABASE_URL.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al validar token: {error_msg}",
        )
