"""
Plan model - SQLAlchemy ORM definition.
Corresponds to 'planes' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Date, Time, Boolean, Numeric, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class Plan(Base):
    """
    Plan model representing service plans.
    """
    __tablename__ = "planes"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Plan Information
    estado = Column(Boolean, nullable=True, default=True)
    nombre = Column(String(100), nullable=False)
    servicios_asociados = Column(ARRAY(String(200)), nullable=True, default=list)
    fecha_inicio = Column(Date, nullable=True)
    fecha_final = Column(Date, nullable=True)
    descripcion = Column(Text, nullable=True)
    
    # Horarios
    hora_inicio = Column(Time, nullable=True)  # Hora en la que puede iniciar el servicio
    hora_final = Column(Time, nullable=True)  # Hora en la que puede finalizar el servicio
    horas_servicio = Column(Integer, nullable=True)  # Horas de trabajo máximo
    
    # Precio
    precio = Column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservas = relationship(
        "Reserva",
        back_populates="plan"
    )
    
    def __repr__(self):
        return f"<Plan {self.nombre}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "estado": self.estado,
            "nombre": self.nombre,
            "servicios_asociados": self.servicios_asociados,
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
