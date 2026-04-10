from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .planes import router as planes_router
from .reservas import router as reservas_router
from .ubicaciones import router as ubicaciones_router
from .dashboard import router as dashboard_router
from .notificaciones import router as notificaciones_router
from .pqrs import router as pqrs_router
from .calificaciones import router as calificaciones_router
from .actividades import router as actividades_router

__all__ = [
    "auth_router",
    "usuarios_router",
    "planes_router",
    "reservas_router",
    "ubicaciones_router",
    "dashboard_router",
    "notificaciones_router",
    "pqrs_router",
    "calificaciones_router",
    "actividades_router",
]
