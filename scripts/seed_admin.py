"""
seed_admin.py
=============
Vacía completamente la base de datos (solo tablas propias de la aplicación),
crea el usuario administrador en Supabase Auth y luego inserta el perfil en la BD.

Uso:
    uv run python scripts/seed_admin.py
"""
import sys
import os
from datetime import date, datetime

# Agregar la raíz del proyecto al path y evitar imports circulares a través de __init__
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Importar config directamente para evitar el circular en app/core/__init__.py
import importlib
import app.core.config  # noqa: F401  — precarga sin pasar por core/__init__

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from supabase import create_client

# ---------------------------------------------------------------------------
# Conexión directa (sin pasar por app.infrastructure.database)
# ---------------------------------------------------------------------------
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# Orden inverso a las FK para truncar sin violar restricciones
# ---------------------------------------------------------------------------
TABLAS_TRUNCAR = [
    "calificaciones",
    "pqrs",
    "notificaciones_servicio",
    "reservas",
    "plan_actividades",
    "actividades",
    "planes",
    "ubicacion_servicio",
    "usuarios",
]

ADMIN = {
    "nombre": "Admin",
    "apellido": "Reluzca",
    "correo": "administrador1reluzca@gmail.com",
    "password": "+Admin1reluzca01012001+",
    "telefono": "3148879926",
    "documento": "79691708",
    "tipo_persona": "natural",
    "fecha_nacimiento": date(2003, 5, 15),
    "rol": "admin",
    "estado": "activo",
}


def vaciar_bd(db) -> None:
    print("⚠️  Vaciando base de datos...")
    for tabla in TABLAS_TRUNCAR:
        existe = db.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t"
        ), {"t": tabla}).fetchone()
        if existe:
            db.execute(text(f'TRUNCATE TABLE "{tabla}" RESTART IDENTITY CASCADE'))
            print(f"   ✓ {tabla} vaciada")
        else:
            print(f"   — {tabla} no existe, omitida")
    db.commit()
    print("✅ Base de datos vaciada.\n")


def crear_admin(db) -> None:
    print("👤 Creando usuario administrador en Supabase Auth...")

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        print("❌ ERROR: SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados en .env")
        sys.exit(1)

    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # 1. Crear (o recuperar) el usuario en Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": ADMIN["correo"],
            "password": ADMIN["password"],
            "email_confirm": True,
        })
        admin_id = auth_response.user.id
        print(f"   ✓ Usuario creado en Supabase Auth: {admin_id}")
    except Exception as e:
        error_msg = str(e)
        # Si ya existe, buscarlo
        if "already" in error_msg.lower() or "duplicate" in error_msg.lower():
            print("   ℹ️  El usuario ya existe en Supabase Auth. Buscando su UUID...")
            users_page = supabase.auth.admin.list_users()
            existing = next(
                (u for u in users_page if u.email == ADMIN["correo"]), None
            )
            if not existing:
                print(f"❌ No se pudo obtener el UUID del admin: {error_msg}")
                sys.exit(1)
            admin_id = existing.id
            print(f"   ✓ UUID encontrado: {admin_id}")
        else:
            print(f"❌ Error al crear en Supabase Auth: {error_msg}")
            sys.exit(1)

    # 2. Insertar perfil en la tabla usuarios (sin columna password)
    now = datetime.utcnow()
    db.execute(text("""
        INSERT INTO usuarios (
            id, nombre, apellido, correo, telefono,
            documento, tipo_persona, fecha_nacimiento,
            rol, estado, fecha_registro, created_at, updated_at
        ) VALUES (
            :id, :nombre, :apellido, :correo, :telefono,
            :documento, :tipo_persona, :fecha_nacimiento,
            :rol, :estado, :fecha_registro, :created_at, :updated_at
        )
    """), {
        "id": admin_id,
        "nombre": ADMIN["nombre"],
        "apellido": ADMIN["apellido"],
        "correo": ADMIN["correo"],
        "telefono": ADMIN["telefono"],
        "documento": ADMIN["documento"],
        "tipo_persona": ADMIN["tipo_persona"],
        "fecha_nacimiento": ADMIN["fecha_nacimiento"],
        "rol": ADMIN["rol"],
        "estado": ADMIN["estado"],
        "fecha_registro": now,
        "created_at": now,
        "updated_at": now,
    })
    db.commit()
    print(f"✅ Administrador creado:")
    print(f"   ID:      {admin_id}")
    print(f"   Nombre:  {ADMIN['nombre']} {ADMIN['apellido']}")
    print(f"   Correo:  {ADMIN['correo']}")
    print(f"   Rol:     {ADMIN['rol']}")
    print(f"   Estado:  {ADMIN['estado']}")


def main() -> None:
    db = SessionLocal()
    try:
        vaciar_bd(db)
        crear_admin(db)
        print("\n🎉 Listo. La base de datos tiene únicamente al superadmin.")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
