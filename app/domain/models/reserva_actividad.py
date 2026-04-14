"""
ReservaActividad model - tracks planned vs executed activities per reservation.
"""
from sqlalchemy import Column, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class ReservaActividad(Base):
    """
    Links a reservation to specific activities.
    programada=True means it was scheduled; ejecutada=True means it was done.
    """
    __tablename__ = "reservas_actividades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False)
    id_actividad = Column(UUID(as_uuid=True), ForeignKey("actividades.id", ondelete="CASCADE"), nullable=False)
    programada = Column(Boolean, default=True, nullable=False)
    ejecutada = Column(Boolean, default=False, nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relationships
    reserva = relationship("Reserva", back_populates="actividades_detalle")
    actividad = relationship("Actividad")

    def __repr__(self):
        return f"<ReservaActividad reserva={self.id_reserva} actividad={self.id_actividad}>"
