"""
Models package - Import all models to ensure SQLAlchemy can resolve relationships.
All models must be imported here to avoid circular import issues.
"""
from app.core.database import Base

# Import models in order to avoid circular dependencies
from app.models.usuario import Usuario
from app.models.plan import Plan
from app.models.ubicacion import UbicacionServicio
from app.models.reserva import Reserva
from app.models.notificacion import NotificacionServicio
from app.models.pqrs import PQRS
from app.models.calificacion import Calificacion

__all__ = [
    "Base",
    "Usuario",
    "Plan",
    "UbicacionServicio",
    "Reserva",
    "NotificacionServicio",
    "PQRS",
    "Calificacion",
]
