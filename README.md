# 🌟 Reluzca Backend - FastAPI

Backend moderno y de alto rendimiento para la plataforma Reluzca, construido con FastAPI y arquitectura en capas.

## � Documentación

- **[CONFIG_STRUCTURE.md](CONFIG_STRUCTURE.md)** - Estructura de configuración y variables de entorno
- **[CONFIG_MIGRATION.md](CONFIG_MIGRATION.md)** - Guía de migración de configuración
- **[AWS_LAMBDA_DEPLOYMENT.md](AWS_LAMBDA_DEPLOYMENT.md)** - Despliegue en AWS Lambda con ECR
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Guía de desarrollo local
- **[AUTHENTICATION.md](AUTHENTICATION.md)** - Sistema de autenticación JWT

## 🚀 Características

- **Framework**: FastAPI (Python 3.11+)
- **Base de datos**: PostgreSQL con SQLAlchemy
- **Autenticación**: JWT (JSON Web Tokens)
- **Arquitectura**: Capas (Controllers/Routers → Services → Repositories → Models)
- **Documentación**: Swagger UI automática en `/docs`
- **Validación**: Pydantic para validación de datos
- **Seguridad**: Bcrypt para hashing de contraseñas
- **Gestor de paquetes**: uv (ultra rápido)
- **Deploy**: AWS Lambda con ECR (Elastic Container Registry)

## 🏗️ Arquitectura

Este proyecto sigue una arquitectura en capas limpia y escalable:

```
back-reluzca/
├── app/
│   ├── api/               # Routers/Endpoints (Capa de presentación)
│   │   ├── auth.py        # Autenticación y registro
│   │   ├── usuarios.py    # Endpoints de usuarios
│   │   ├── planes.py      # Endpoints de planes
│   │   ├── reservas.py    # Endpoints de reservas
│   │   └── ubicaciones.py # Endpoints de ubicaciones
│   │
│   ├── core/              # Configuración central y utilidades
│   │   ├── config.py      # Configuración de la aplicación
│   │   ├── database.py    # Configuración de base de datos
│   │   ├── security.py    # Seguridad y autenticación
│   │   └── dependencies.py # Dependencias de FastAPI
│   │
│   ├── models/            # Modelos de SQLAlchemy (capa de datos)
│   │   ├── usuario.py
│   │   ├── plan.py
│   │   ├── reserva.py
│   │   └── ubicacion.py
│   │
│   ├── repositories/      # Capa de acceso a datos
│   │   ├── usuario_repository.py
│   │   ├── plan_repository.py
│   │   ├── reserva_repository.py
│   │   └── ubicacion_repository.py
│   │
│   ├── schemas/           # Modelos Pydantic (validación)
│   │   ├── usuario.py
│   │   ├── plan.py
│   │   ├── reserva.py
│   │   └── ubicacion.py
│   │
│   └── services/          # Lógica de negocio
│       ├── auth_service.py
│       ├── usuario_service.py
│       ├── plan_service.py
│       ├── reserva_service.py
│       └── ubicacion_service.py
│
├── .venv/               # Entorno virtual (creado con uv)
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias (referencia, no se usa)
├── .env                 # Variables de entorno (no en Git)
├── .env.example         # Ejemplo de variables de entorno
└── README.md            # Este archivo
│   │   ├── plan.py
│   │   └── ...
│   │
│   ├── schemas/           # Schemas de Pydantic (validación)
│   │   ├── usuario.py
│   │   ├── reserva.py
│   │   ├── plan.py
│   │   └── ...
│   │
│   ├── repositories/      # Capa de acceso a datos
│   │   ├── usuario_repository.py
│   │   ├── reserva_repository.py
│   │   └── ...
│   │
│   ├── services/          # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── usuario_service.py
│   │   ├── reserva_service.py
│   │   └── ...
│   │
│   ├── api/              # Endpoints (controladores)
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── usuarios.py
│   │   │   ├── reservas.py
│   │   │   ├── planes.py
│   │   │   └── ...
│   │   └── dependencies.py
│   │
│   ├── utils/            # Utilidades y helpers
│   │   ├── email.py
│   │   ├── validators.py
│   │   └── ...
│   │
│   └── main.py           # Punto de entrada de la aplicación
│
├── alembic/              # Migraciones de base de datos
├── tests/                # Tests
├── .env                  # Variables de entorno (no commitear)
├── .env.example          # Ejemplo de variables de entorno
├── requirements.txt      # Dependencias
└── README.md            # Este archivo
```

## 🚀 Características

- ⚡ **FastAPI**: Framework moderno y de alto rendimiento
- 🔐 **JWT Authentication**: Autenticación segura con tokens
- 🗄️ **PostgreSQL**: Base de datos robusta con Supabase
- 📧 **Email**: Sistema de verificación por correo
- 🏗️ **Arquitectura en Capas**: Código organizado y mantenible
- 📝 **Pydantic**: Validación automática de datos
- 🔄 **Async/Await**: Operaciones asíncronas para mejor rendimiento
- 📊 **SQLAlchemy 2.0**: ORM moderno con soporte async
- 🧪 **Testing**: Configurado para pruebas automatizadas

## 🛠️ Instalación

### Prerrequisitos

- Python 3.11+
- PostgreSQL
- uv (gestor de paquetes ultra rápido)

### Instalación de uv

Si no tienes `uv` instalado:

**Windows**:
```bash
pip install uv
```

**Linux/Mac**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Pasos

1. **Configurar el proyecto**:
```bash
# Ejecuta el script de setup que crea el entorno virtual e instala dependencias
setup.bat  # Windows
./setup.sh # Linux/Mac
```

2. **Configurar variables de entorno**:
```bash
# Copia el archivo de ejemplo y edita con tus credenciales
cp .env.example .env
# Edita .env con tus credenciales de PostgreSQL
```

3. **Iniciar servidor**:
```bash
# El script aauth/register` - Registro de usuarios
- `POST /api/auth/login` - Inicio de sesión (form-data)
- `POST /api/auth/login/json` - Inicio de sesión (JSON)
- `GET /api/auth/me` - Perfil del usuario autenticado

### Usuarios
- `GET /api/usuarios/` - Listar usuarios (admin)
- `GET /api/usuarios/{id}` - Obtener usuario
- `POST /api/usuarios/` - Crear usuario (admin)
- `PUT /api/usuarios/{id}` - Actualizar usuario
- `DELETE /api/usuarios/{id}` - Eliminar usuario (admin)
- `GET /api/usuarios/rol/{rol}` - Usuarios por rol (admin)

### Planes
- `GET /api/planes/` - Listar planes
- `GET /api/planes/{id}` - Obtener plan
- `POST /api/planes/` - Crear plan (admin)
- `PUT /api/planes/{id}` - Actualizar plan (admin)
- `DELETE /api/planes/{id}` - Eliminar plan (admin)

### Reservas
- `GET /api/reservas/` - Listar reservas (admin/empleada)
- `GET /api/reservas/cliente/{id}` - Reservas por cliente
- `GET /api/reservas/empleada/{id}` - Reservas por empleada
- `POST /api/reservas/` - Crear reserva
- `PUT /api/reservas/{id}` - Actualizar reserva (admin/empleada)
- `PATCH /api/reservas/{id}/cancel` - Cancelar reserva

### Ubicaciones
**Base de Datos**:
- `DB_HOST`: Host de PostgreSQL (default: localhost)
- `DB_PORT`: Puerto de PostgreSQL (default: 5432)
- `DB_NAME`: Nombre de la base de datos (default: reluzca_db)
- `DB_USER`: Usuario de PostgreSQL
- `DB_PASSWORD`: Contraseña de PostgreSQL

**Seguridad**:
- `SECRET_KEY`: Llave secreta de la aplicación (mínimo 32 caracteres)
- `ALGORITHM`: Algoritmo JWT (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Duración del token (default: 30)

**CORS**:
- `BACKEND_CORS_ORIGINS`: Orígenes permitidos en formato JSON arrayió
### Autenticación
- `POST /api/v1/auth/signup` - Registro de usuarios
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/verify-email` - Verificación de correo
- `POST /api/v1/auth/refresh` - Refrescar token
- `POST /api/v1/auth/logout` - Cerrar sesión

### Usuarios
- `GET /api/v1/users/me` - Perfil del usuario autenticado
- `PUT /api/v1/users/me` - Actualizar perfil
- `GET /api/v1/users/` - Listar usuarios (admin)
- `GET /api/v1/users/{id}` - Obtener usuario por ID

### Reservas
- `GET /api/v1/reservas/` - Listar reservas
- `POST /api/v1/reservas/` - Crear reserva
- `GET /api/v1/reservas/{id}` - Obtener reserva
- `PUT /api/v1/reservas/{id}` - Actualizar reserva
- `DELETE /api/v1/reservas/{id}` - Eliminar reserva

### Planes
- `GET /api/v1/planes/` - Listar planes
- `POST /api/v1/planes/` - Crear plan (admin)
- `GET /api/v1/planes/{id}` - Obtener plan
- `PUT /api/v1/planes/{id}` - Actualizar plan (admin)

## 🔑 Variables de Entorno

Ver `.env.example` para todas las variables disponibles. Las principales son:

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Llave secreta de la aplicación
- `JWT_SECRET_KEY`: Llave para tokens JWT
- `EMAIL_HOST_USER`: Usuario de correo SMTP
- `EMAIL_HOST_PASSWORD`: Contraseña de correo SMTP

## 🧪 Testing

```bash
pytest
```

## 📝 Documentación API
Ventajas sobre Django

Este backend es una migración del backend original en Django, manteniendo toda la lógica de negocio pero aprovechando las ventajas de FastAPI:

- ⚡ **3-5x más rápido** que Django
- 📝 **Documentación automática** (Swagger UI + ReDoc)
- 🔄 **Soporte async nativo** para mejor rendimiento
- ✅ **Validación automática** con Pydantic
- 🎯 **Type hints** y autocompletado mejorado
- 🚀 **uv**: Instalación de dependencias ultra rápida (10-100x más rápido que pip)
- 🏗️ **Arquitectura en capas** clara y mantenible

### 📋 Documentación Adicional

- [AUTHENTICATION.md](AUTHENTICATION.md) - Guía completa de autenticación y JWT
- [DEVELOPMENT.md](DEVELOPMENT.md) - Guía para desarrolladores
- [DJANGO_VS_FASTAPI.md](DJANGO_VS_FASTAPI.md) - Comparación detallada Django vs FastAPIlimpio y arquitectura en capas. Al contribuir:

1. Mantén la separación de responsabilidades
2. Usa type hints en Python
3. Documenta funciones y clases
4. Escribe tests para nuevas funcionalidades

## 📄 Licencia

Propiedad de Reluzca © 2024

## 🚀 Migración desde Django

Este backend es una migración del backend original en Django, manteniendo toda la lógica de negocio pero aprovechando las ventajas de FastAPI:

- ⚡ 2-3x más rápido que Django
- 📝 Documentación automática
- 🔄 Soporte async nativo
- ✅ Validación automática con Pydantic
- 🎯 Type hints y autocompletado mejorado

## 📞 Soporte

Para preguntas o soporte, contacta al equipo de desarrollo de Reluzca.
