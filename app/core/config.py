"""Configuración centralizada del proyecto Reluzca usando Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada del proyecto Reluzca."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== Aplicación ====================
    PROJECT_NAME: str = "Reluzca API"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # ==================== Base de Datos ====================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "reluzca_db"
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # ==================== Seguridad ====================
    SECRET_KEY: str = "change-me"

    # ==================== CORS ====================
    # Se lee desde .env como string separado por comas
    CORS_ORIGINS: str = Field(default="")

    # ==================== Email ====================
    EMAIL_BACKEND: str = "smtp"
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USER: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    DEFAULT_FROM_EMAIL: str = ""
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 48

    # ==================== Supabase ====================
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # ==================== Properties ====================
    @property
    def supabase_jwt_issuer(self) -> str:
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL}/auth/v1"
        return ""

    @property
    def cors_origins(self) -> List[str]:
        """Convierte CORS_ORIGINS string a lista."""
        if not self.CORS_ORIGINS:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:8000",
                "http://localhost:8000"
            ]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def DATABASE_URL(self) -> str:
        """URL async para SQLAlchemy (asyncpg)."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL sync para Alembic (psycopg2)."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def is_development(self) -> bool:
        """Verifica si está en modo desarrollo."""
        return self.DEBUG

    @field_validator("DEFAULT_FROM_EMAIL")
    @classmethod
    def set_default_from_email(cls, v, info):
        """Establece el email por defecto si no está configurado."""
        if not v and info.data.get("EMAIL_HOST_USER"):
            return info.data.get("EMAIL_HOST_USER")
        return v


@lru_cache
def get_settings() -> Settings:
    """Singleton de settings (se carga una sola vez)."""
    return Settings()


# Instancia global
settings = get_settings()
