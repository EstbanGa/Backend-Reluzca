"""
NotificacionesServicio model - SQLAlchemy ORM definition.
Corresponds to 'notificaciones_servicio' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class NotificacionServicio(Base):
    """
    NotificacionServicio model representing service notifications.
    """
    __tablename__ = "notificaciones_servicio"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=False)
    id_cliente = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    
    # Notification Information
    tipo_notificacion = Column(String(30), nullable=False)  # cambio_estado, recordatorio, cancelacion, etc
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    
    # Relationships
    reserva = relationship(
        "Reserva",
        back_populates="notificaciones"
    )
    
    cliente = relationship(
        "Usuario",
        foreign_keys=[id_cliente],
        back_populates="notificaciones"
    )
    
    def __repr__(self):
        return f"<NotificacionServicio {self.tipo_notificacion} - {self.mensaje[:50]}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_reserva": str(self.id_reserva),
            "id_cliente": str(self.id_cliente),
            "tipo_notificacion": self.tipo_notificacion,
            "mensaje": self.mensaje,
            "leida": self.leida,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
