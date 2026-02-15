"""
UbicacionServicio model - SQLAlchemy ORM definition.
Corresponds to 'ubicacion_servicio' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class UbicacionServicio(Base):
    """
    UbicacionServicio model representing service locations.
    """
    __tablename__ = "ubicacion_servicio"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    
    # Location Information
    nombre = Column(String(100), nullable=False)
    tamaño = Column(JSON, nullable=True)  # {"metros_cuadrados": 100, "tipo": "apartamento"}
    baños = Column(Integer, nullable=True)
    pisos = Column(Integer, nullable=True)
    ubicacion = Column(JSON, nullable=True)  # {"lat": 4.123, "lng": -74.123, "direccion": "..."}
    nombre_lugar = Column(String(100), nullable=True)
    tipo_lugar = Column(String(20), nullable=True)  # casa, apartamento, oficina, etc
    estado = Column(Boolean, default=True)
    descripcion = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    usuario = relationship(
        "Usuario",
        back_populates="ubicaciones"
    )
    
    reservas = relationship(
        "Reserva",
        back_populates="lugar"
    )
    
    def __repr__(self):
        return f"<UbicacionServicio {self.nombre}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_usuario": str(self.id_usuario),
            "nombre": self.nombre,
            "tamaño": self.tamaño,
            "baños": self.baños,
            "pisos": self.pisos,
            "ubicacion": self.ubicacion,
            "nombre_lugar": self.nombre_lugar,
            "tipo_lugar": self.tipo_lugar,
            "estado": self.estado,
            "descripcion": self.descripcion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UbicacionesEmpleada(Base):
    """
    UbicacionesEmpleada model representing employee location tracking.
    """
    __tablename__ = "ubicaciones_empleada"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_empleada = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    id_reserva = Column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=True)
    
    # Location Tracking Information
    fecha_hora = Column(DateTime, nullable=True)
    coordenadas = Column(JSON, nullable=False)  # {"lat": 4.123, "lng": -74.123}
    tipo_evento = Column(String(20), nullable=True)  # inicio, en_camino, llegada, fin
    distancia_destino_metros = Column(Numeric(8, 2), nullable=True)
    estado = Column(String(20), nullable=True)
    precision_metros = Column(Numeric(8, 2), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    
    # Relationships
    empleada = relationship(
        "Usuario",
        back_populates="ubicaciones_empleada"
    )
    
    reserva = relationship(
        "Reserva",
        back_populates="ubicaciones_empleada"
    )
    
    def __repr__(self):
        return f"<UbicacionesEmpleada {self.id} - {self.tipo_evento}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_empleada": str(self.id_empleada),
            "id_reserva": str(self.id_reserva) if self.id_reserva else None,
            "fecha_hora": self.fecha_hora.isoformat() if self.fecha_hora else None,
            "coordenadas": self.coordenadas,
            "tipo_evento": self.tipo_evento,
            "distancia_destino_metros": float(self.distancia_destino_metros) if self.distancia_destino_metros else None,
            "estado": self.estado,
            "precision_metros": float(self.precision_metros) if self.precision_metros else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
