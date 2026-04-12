"""Core module initialization."""
from app.core.config import settings, get_settings
from app.infrastructure.database import get_db, Base, engine
from app.infrastructure.security import verify_supabase_token, SupabaseTokenData
from app.presentation.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_cliente,
    require_empleada,
    require_role,
)

__all__ = [
    "settings",
    "get_settings",
    "get_db",
    "Base",
    "engine",
    "verify_supabase_token",
    "SupabaseTokenData",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_cliente",
    "require_empleada",
    "require_role",
]
