"""
drop_django_tables.py
=====================
Elimina las tablas heredadas de Django que ya no se usan en el backend FastAPI/Supabase.

Uso:
    uv run python scripts/drop_django_tables.py

Tablas eliminadas (con CASCADE para no romper FK):
  - auth_group, auth_group_permissions, auth_permission
  - auth_user, auth_user_groups, auth_user_user_permissions
  - django_admin_log, django_content_type, django_migrations, django_session
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sqlalchemy import create_engine, text
from app.core.config import settings

DJANGO_TABLES = [
    # Dependientes primero para evitar problemas de FK
    "auth_user_user_permissions",
    "auth_user_groups",
    "auth_group_permissions",
    "django_admin_log",
    # Tablas base
    "auth_user",
    "auth_permission",
    "auth_group",
    "django_content_type",
    "django_migrations",
    "django_session",
]


def drop_django_tables() -> None:
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)

    with engine.begin() as conn:
        print("🗑️  Eliminando tablas de Django...")
        for tabla in DJANGO_TABLES:
            existe = conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :t"
            ), {"t": tabla}).fetchone()

            if existe:
                conn.execute(text(f'DROP TABLE IF EXISTS "{tabla}" CASCADE'))
                print(f"   ✓ Tabla '{tabla}' eliminada")
            else:
                print(f"   — Tabla '{tabla}' no existe, omitida")

    print("\n✅ Limpieza de tablas Django completada.")


if __name__ == "__main__":
    drop_django_tables()
