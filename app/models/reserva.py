"""
Reserva model - SQLAlchemy ORM definition.
Corresponds to 'reservas' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Date, Time, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Reserva(Base):
    """
    Reserva model representing service bookings.
    """
    __tablename__ = "reservas"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    id_empleada = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    id_plan = Column(UUID(as_uuid=True), ForeignKey("planes.id"), nullable=True)
    id_lugar = Column(UUID(as_uuid=True), ForeignKey("ubicacion_servicio.id"), nullable=True)
    
    # Reservation Information
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_final = Column(Time, nullable=False)
    estado = Column(String(20), nullable=True, default="pendiente")  # pendiente, confirmada, en_proceso, completada, cancelada
    estado_pago = Column(String(20), nullable=True, default="SIN_PAGAR")  # SIN_PAGAR, PAGADO, REEMBOLSADO
    descripcion = Column(Text, nullable=True)
    precio_total = Column(Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cliente = relationship(
        "Usuario",
        foreign_keys=[id_usuario],
        back_populates="reservas_cliente"
    )
    
    empleada = relationship(
        "Usuario",
        foreign_keys=[id_empleada],
        back_populates="reservas_empleada"
    )
    
    plan = relationship(
        "Plan",
        back_populates="reservas"
    )
    
    lugar = relationship(
        "UbicacionServicio",
        back_populates="reservas"
    )
    
    # PQRS relacionados
    pqrs = relationship(
        "PQRS",
        foreign_keys="PQRS.id_reserva",
        back_populates="reserva"
    )
    
    # Notificaciones
    notificaciones = relationship(
        "NotificacionServicio",
        foreign_keys="NotificacionServicio.id_reserva",
        back_populates="reserva"
    )
    
    # Calificaciones
    calificaciones = relationship(
        "Calificacion",
        foreign_keys="Calificacion.id_reserva",
        back_populates="reserva"
    )
    
    # Ubicaciones de empleada
    ubicaciones_empleada = relationship(
        "UbicacionesEmpleada",
        back_populates="reserva"
    )
    
    # Pago - COMENTADO: modelo no implementado aún
    # pago = relationship(
    #     "Pago",
    #     back_populates="reserva",
    #     uselist=False
    # )
    
    def __repr__(self):
        return f"<Reserva {self.id} - {self.fecha}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "id_usuario": str(self.id_usuario),
            "id_empleada": str(self.id_empleada) if self.id_empleada else None,
            "id_plan": str(self.id_plan) if self.id_plan else None,
            "id_lugar": str(self.id_lugar) if self.id_lugar else None,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora_inicio": self.hora_inicio.strftime("%H:%M:%S") if self.hora_inicio else None,
            "hora_final": self.hora_final.strftime("%H:%M:%S") if self.hora_final else None,
            "estado": self.estado,
            "estado_pago": self.estado_pago,
            "descripcion": self.descripcion,
            "precio_total": float(self.precio_total) if self.precio_total else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
