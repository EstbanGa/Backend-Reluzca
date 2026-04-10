"""
Calificacion model - SQLAlchemy ORM definition.
Corresponds to 'calificaciones' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class Calificacion(Base):
    """
    Calificacion model for rating services and employees.
    """
    __tablename__ = "calificaciones"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=False)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    id_empleada = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    
    # Rating Information
    calificacion_servicio = Column(Integer, nullable=False)  # 1-5 stars
    calificacion_empleada = Column(Integer, nullable=True)  # 1-5 stars
    comentario = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reserva = relationship(
        "Reserva",
        foreign_keys=[id_reserva],
        back_populates="calificaciones"
    )
    
    usuario = relationship(
        "Usuario",
        foreign_keys=[id_usuario],
        back_populates="calificaciones_usuario"
    )
    
    empleada = relationship(
        "Usuario",
        foreign_keys=[id_empleada],
        back_populates="calificaciones_empleada"
    )
    
    def __repr__(self):
        return f"<Calificacion servicio={self.calificacion_servicio} empleada={self.calificacion_empleada}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_reserva": str(self.id_reserva),
            "id_usuario": str(self.id_usuario),
            "id_empleada": str(self.id_empleada) if self.id_empleada else None,
            "calificacion_servicio": self.calificacion_servicio,
            "calificacion_empleada": self.calificacion_empleada,
            "comentario": self.comentario,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
