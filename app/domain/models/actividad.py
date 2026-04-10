"""
Actividad model - SQLAlchemy ORM definition.
Corresponds to 'actividades' table in PostgreSQL.
Individual services that can be part of a plan or reserved standalone.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Numeric, Integer, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


plan_actividades = Table(
    "plan_actividades",
    Base.metadata,
    Column(
        "id_plan",
        UUID(as_uuid=True),
        ForeignKey("planes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "id_actividad",
        UUID(as_uuid=True),
        ForeignKey("actividades.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Actividad(Base):
    """
    Actividad model representing individual service activities.
    Can belong to one or more plans (M2M), or be reserved independently.
    """
    __tablename__ = "actividades"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Activity Information
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio_unitario = Column(Numeric(10, 2), nullable=True)
    duracion_estimada_minutos = Column(Integer, nullable=True)
    activa = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    planes = relationship(
        "Plan",
        secondary=plan_actividades,
        back_populates="actividades",
    )

    def __repr__(self):
        return f"<Actividad {self.nombre}>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio_unitario": float(self.precio_unitario) if self.precio_unitario else None,
            "duracion_estimada_minutos": self.duracion_estimada_minutos,
            "activa": self.activa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
