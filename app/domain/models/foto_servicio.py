"""
FotoServicio model - photos of a service/reservation.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class FotoServicio(Base):
    """
    Stores photo data (base64 or URL) associated with a reservation/service.
    id_actividad links the photo to a specific checklist item (ReservaActividad.id).
    """
    __tablename__ = "fotos_servicio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False)
    url_foto = Column(Text, nullable=False)  # base64 data URL or cloud URL
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(20), nullable=True, default="durante")  # antes, durante, despues
    id_actividad = Column(UUID(as_uuid=True), nullable=True)  # links to reservas_actividades.id
    subida_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relationships
    reserva = relationship("Reserva", back_populates="fotos")
    empleada = relationship("Usuario", foreign_keys=[subida_por])

    def __repr__(self):
        return f"<FotoServicio reserva={self.id_reserva} tipo={self.tipo}>"
