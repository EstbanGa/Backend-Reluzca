"""
Plan model - SQLAlchemy ORM definition.
Corresponds to 'planes' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Date, Time, Boolean, Numeric, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base
from app.domain.models.actividad import plan_actividades


class Plan(Base):
    """
    Plan model representing service plans.
    tipo_plan can be 'full' (all actividades included) or 'a_la_carte' (client picks).
    """
    __tablename__ = "planes"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan Information
    estado = Column(Boolean, nullable=True, default=True)
    nombre = Column(String(100), nullable=False)
    tipo_plan = Column(String(20), nullable=True, default="full")  # full, a_la_carte
    fecha_inicio = Column(Date, nullable=True)
    fecha_final = Column(Date, nullable=True)
    descripcion = Column(Text, nullable=True)

    # Horarios
    hora_inicio = Column(Time, nullable=True)
    hora_final = Column(Time, nullable=True)
    horas_servicio = Column(Integer, nullable=True)

    # Precio
    precio = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reservas = relationship(
        "Reserva",
        back_populates="plan",
    )

    actividades = relationship(
        "Actividad",
        secondary=plan_actividades,
        back_populates="planes",
    )

    def __repr__(self):
        return f"<Plan {self.nombre}>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "estado": self.estado,
            "nombre": self.nombre,
            "tipo_plan": self.tipo_plan,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_final": self.fecha_final.isoformat() if self.fecha_final else None,
            "descripcion": self.descripcion,
            "hora_inicio": self.hora_inicio.strftime("%H:%M:%S") if self.hora_inicio else None,
            "hora_final": self.hora_final.strftime("%H:%M:%S") if self.hora_final else None,
            "horas_servicio": self.horas_servicio,
            "precio": float(self.precio) if self.precio else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
