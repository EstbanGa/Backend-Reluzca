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
    NotificacionServicio model representing notifications sent to users.
    Supports reserva-based, PQRS-based, and general notifications.
    Destinations can be clientes or empleadas.
    """
    __tablename__ = "notificaciones_servicio"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys (all nullable — notification may relate to reserva, pqrs, or neither)
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=True)
    id_pqrs = Column(UUID(as_uuid=True), ForeignKey("pqrs.id"), nullable=True)
    id_usuario_destino = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    # Notification Information
    tipo = Column(String(30), nullable=False)  # sistema, manual, recordatorio, confirmacion, pago, pqrs
    canal = Column(String(10), nullable=False, default="in_app")  # in_app, email, ambos
    mensaje = Column(Text, nullable=False)
    leida = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relationships
    reserva = relationship(
        "Reserva",
        back_populates="notificaciones",
    )

    pqrs = relationship(
        "PQRS",
        foreign_keys=[id_pqrs],
    )

    usuario_destino = relationship(
        "Usuario",
        foreign_keys=[id_usuario_destino],
        back_populates="notificaciones",
    )

    def __repr__(self):
        return f"<NotificacionServicio {self.tipo} - {self.mensaje[:50]}>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_reserva": str(self.id_reserva) if self.id_reserva else None,
            "id_pqrs": str(self.id_pqrs) if self.id_pqrs else None,
            "id_usuario_destino": str(self.id_usuario_destino),
            "tipo": self.tipo,
            "canal": self.canal,
            "mensaje": self.mensaje,
            "leida": self.leida,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
