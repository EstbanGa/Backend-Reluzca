"""
PQRS model - SQLAlchemy ORM definition.
Corresponds to 'pqrs' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class PQRS(Base):
    """
    PQRS model representing peticiones, quejas, reclamos y sugerencias.
    """
    __tablename__ = "pqrs"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    id_empleada = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=True)
    
    # PQRS Information
    tipo = Column(String(20), nullable=False)  # peticion, queja, reclamo, sugerencia
    fecha_creacion = Column(DateTime, nullable=True, default=datetime.utcnow)
    descripcion = Column(Text, nullable=False)
    fecha_resolucion = Column(DateTime, nullable=True)
    estado = Column(String(20), nullable=True, default="pendiente")  # pendiente, en_proceso, resuelto, cerrado
    respuesta = Column(Text, nullable=True)
    prioridad = Column(String(10), nullable=True, default="media")  # baja, media, alta
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    usuario = relationship(
        "Usuario",
        foreign_keys=[id_usuario],
        back_populates="pqrs_usuario"
    )
    
    empleada = relationship(
        "Usuario",
        foreign_keys=[id_empleada],
        back_populates="pqrs_empleada"
    )
    
    reserva = relationship(
        "Reserva",
        foreign_keys=[id_reserva],
        back_populates="pqrs"
    )
    
    def __repr__(self):
        return f"<PQRS {self.tipo} - {self.estado}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_usuario": str(self.id_usuario),
            "id_empleada": str(self.id_empleada) if self.id_empleada else None,
            "id_reserva": str(self.id_reserva) if self.id_reserva else None,
            "tipo": self.tipo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "descripcion": self.descripcion,
            "fecha_resolucion": self.fecha_resolucion.isoformat() if self.fecha_resolucion else None,
            "estado": self.estado,
            "respuesta": self.respuesta,
            "prioridad": self.prioridad,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
