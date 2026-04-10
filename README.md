# Reluzca Backend — FastAPI

API REST para la plataforma Reluzca, sistema de gestión de servicios de limpieza. Construida con FastAPI siguiendo Clean Architecture.

## Stack tecnológico

| Categoría | Tecnología |
|---|---|
| Framework | FastAPI 0.115 + Python 3.11+ |
| Base de datos | PostgreSQL + SQLAlchemy 2.0 (síncrono/psycopg2) |
| Migraciones | Alembic |
| Autenticación | JWT (python-jose) + Bcrypt (passlib) |
| Validación | Pydantic v2 + pydantic-settings |
| Email | aiosmtplib |
| Deploy | AWS Lambda (Mangum) |

## Arquitectura

El proyecto sigue Clean Architecture con 4 capas:

```
app/
├── core/                        # Configuración transversal
│   └── config.py                # Settings (pydantic-settings)
│
├── domain/                      # Entidades y contratos del negocio
│   ├── models/                  # Modelos SQLAlchemy (ORM)
│   │   ├── usuario.py
│   │   ├── plan.py
│   │   ├── reserva.py
│   │   ├── ubicacion.py
│   │   ├── calificacion.py
│   │   ├── notificacion.py
│   │   └── pqrs.py
│   └── schemas/                 # Schemas Pydantic (request/response)
│       ├── usuario.py
│       ├── plan.py
│       ├── reserva.py
│       ├── ubicacion.py
│       └── dashboard.py
│
├── application/                 # Casos de uso / lógica de negocio
│   └── services/
│       ├── auth_service.py
│       ├── usuario_service.py
│       ├── plan_service.py
│       ├── reserva_service.py
│       ├── ubicacion_service.py
│       ├── calificacion_service.py
│       ├── notificacion_service.py
│       ├── pqrs_service.py
│       └── dashboard_service.py
│
├── infrastructure/              # Implementaciones técnicas
│   ├── database.py              # Engine, SessionLocal, Base, get_db
│   ├── security.py              # JWT (crear/verificar tokens), hashing
│   ├── auth.py                  # oauth2_scheme (OAuth2PasswordBearer)
│   ├── repositories/            # Acceso a datos (SQLAlchemy)
│   │   ├── usuario_repository.py
│   │   ├── plan_repository.py
│   │   ├── reserva_repository.py
│   │   ├── ubicacion_repository.py
│   │   ├── calificacion_repository.py
│   │   ├── notificacion_repository.py
│   │   ├── pqrs_repository.py
│   │   └── dashboard_repository.py
│   └── integrations/
│       └── email_service.py     # Envío de correos (aiosmtplib)
│
└── presentation/                # Capa HTTP
    ├── dependencies.py          # get_current_user, require_admin, etc.
    └── api/
        └── v1/                  # Endpoints versionados
            ├── auth.py
            ├── usuarios.py
            ├── planes.py
            ├── reservas.py
            ├── ubicaciones.py
            ├── calificaciones.py
            ├── notificaciones.py
            ├── pqrs.py
            └── dashboard.py
```

### Flujo de dependencias

```
presentation → application → domain
                    ↓
             infrastructure
```

Ninguna capa interna conoce a las externas.

## Configuración local

### Requisitos previos

- Python 3.11+
- PostgreSQL (local o remoto)

### Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar migraciones
alembic upgrade head

# 4. Iniciar servidor de desarrollo
uvicorn main:app --reload --port 8000
```

### Variables de entorno

Copia `.env.example` y completa los valores:

```env
# Aplicación
PROJECT_NAME=Reluzca
DEBUG=true
FRONTEND_URL=http://localhost:3000

# Base de datos (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=reluzca
DB_USER=postgres
DB_PASSWORD=tu_password
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# JWT
SECRET_KEY=tu_secret_key
JWT_SECRET_KEY=tu_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=30
JWT_REFRESH_TOKEN_LIFETIME=10080
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Email (SMTP)
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
DEFAULT_FROM_EMAIL=tu_correo@gmail.com
EMAIL_VERIFICATION_EXPIRY_HOURS=48
```

## Endpoints principales

La documentación interactiva completa está disponible en `/docs` (Swagger UI) y `/redoc` cuando el servidor está activo.

Todos los endpoints de negocio llevan el prefijo `/api`.

| Recurso | Prefijo |
|---|---|
| Autenticación | `/api/auth` |
| Usuarios | `/api/usuarios` |
| Planes | `/api/planes` |
| Reservas | `/api/reservas` |
| Ubicaciones | `/api/ubicaciones` |
| Calificaciones | `/api/calificaciones` |
| Notificaciones | `/api/notificaciones` |
| PQRS | `/api/pqrs` |
| Dashboard | `/api/dashboard` |

### Autenticación

```
POST /api/auth/register       Registro de nuevo usuario
POST /api/auth/login          Inicio de sesión (form-data, OAuth2)
POST /api/auth/login/json     Inicio de sesión (JSON)
GET  /api/auth/me             Perfil del usuario autenticado
GET  /api/auth/verify-email   Verificación de correo electrónico
```

### Roles

El sistema maneja 3 roles: `admin`, `cliente`, `empleada`. Las dependencias de autorización se declaran en `app/presentation/dependencies.py`:

- `get_current_user` — cualquier usuario autenticado
- `require_admin` — solo administradores
- `require_cliente` — solo clientes
- `require_empleada` — solo empleadas

## Migraciones de base de datos

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver estado actual
alembic current
```

## Despliegue (AWS Lambda)

El proyecto usa `mangum` como adaptador para ejecutarse en AWS Lambda detrás de API Gateway.

```bash
# Construir imagen Docker
docker build -f Dockerfile.lambda -t reluzca-backend .

# Ver script de despliegue completo
./deploy.ps1
```

## Verificación de salud

```
GET /           → {"message": "Bienvenido a la API de Reluzca", "version": "1.0.0"}
GET /api/health → {"status": "healthy", "service": "reluzca-backend"}
```
