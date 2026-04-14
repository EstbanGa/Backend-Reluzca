"""
Models package - Import all models to ensure SQLAlchemy can resolve relationships.
All models must be imported here to avoid circular import issues.
"""
from app.infrastructure.database import Base

# Import models in order to avoid circular dependencies
from app.domain.models.usuario import Usuario
from app.domain.models.actividad import Actividad, plan_actividades
from app.domain.models.plan import Plan
from app.domain.models.ubicacion import UbicacionServicio, UbicacionesEmpleada
from app.domain.models.reserva import Reserva
from app.domain.models.reserva_actividad import ReservaActividad
from app.domain.models.foto_servicio import FotoServicio
from app.domain.models.notificacion import NotificacionServicio
from app.domain.models.pqrs import PQRS
from app.domain.models.calificacion import Calificacion

__all__ = [
    "Base",
    "Usuario",
    "Actividad",
    "plan_actividades",
    "Plan",
    "UbicacionServicio",
    "UbicacionesEmpleada",
    "Reserva",
    "ReservaActividad",
    "FotoServicio",
    "NotificacionServicio",
    "PQRS",
    "Calificacion",
]
