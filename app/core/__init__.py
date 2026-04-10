"""Core module initialization."""
from app.core.config import settings, get_settings
from app.infrastructure.database import get_db, Base, engine
from app.infrastructure.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_tokens,
    create_email_verification_token,
    verify_email_token,
)
from app.presentation.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_cliente,
    require_empleada,
    require_role,
)

__all__ = [
    # Config
    "settings",
    "get_settings",
    # Database
    "get_db",
    "Base",
    "engine",
    # Security
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_tokens",
    "create_email_verification_token",
    "verify_email_token",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "require_cliente",
    "require_empleada",
    "require_role",
]
