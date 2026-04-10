"""
Usuario model - SQLAlchemy ORM definition.
Corresponds to 'usuarios' table in PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, Date, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database import Base


class Usuario(Base):
    """
    Usuario model representing users in the system.
    Roles: admin, cliente, empleada
    """
    __tablename__ = "usuarios"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Information
    rol = Column(String(20), nullable=False)  # admin, cliente, empleada
    fecha_registro = Column(DateTime, nullable=True, default=datetime.utcnow)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    documento = Column(String(20), unique=True, nullable=True)
    telefono = Column(String(15), nullable=False)
    tipo_persona = Column(String(20), nullable=True)  # natural, juridica
    fecha_nacimiento = Column(Date, nullable=True)
    estado = Column(String(20), nullable=True, default="pendiente")  # activo, inactivo, pendiente
    ranking = Column(Numeric(3, 2), nullable=True)  # For empleadas
    
    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Reservas as cliente
    reservas_cliente = relationship(
        "Reserva",
        foreign_keys="Reserva.id_usuario",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )
    
    # Reservas as empleada
    reservas_empleada = relationship(
        "Reserva",
        foreign_keys="Reserva.id_empleada",
        back_populates="empleada"
    )
    
    # PQRS as usuario
    pqrs_usuario = relationship(
        "PQRS",
        foreign_keys="PQRS.id_usuario",
        back_populates="usuario"
    )
    
    # PQRS as empleada
    pqrs_empleada = relationship(
        "PQRS",
        foreign_keys="PQRS.id_empleada",
        back_populates="empleada"
    )
    
    # Ubicaciones de servicio
    ubicaciones = relationship(
        "UbicacionServicio",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )
    
    # Ubicaciones de empleada
    ubicaciones_empleada = relationship(
        "UbicacionesEmpleada",
        back_populates="empleada"
    )
    
    # Notificaciones
    notificaciones = relationship(
        "NotificacionServicio",
        foreign_keys="NotificacionServicio.id_usuario_destino",
        back_populates="usuario_destino",
    )
    
    # Calificaciones como usuario (cliente que califica)
    calificaciones_usuario = relationship(
        "Calificacion",
        foreign_keys="Calificacion.id_usuario",
        back_populates="usuario"
    )
    
    # Calificaciones como empleada (empleada que recibe calificaciones)
    calificaciones_empleada = relationship(
        "Calificacion",
        foreign_keys="Calificacion.id_empleada",
        back_populates="empleada"
    )
    
    # Pagos - COMENTADO: modelo no implementado aún
    # pagos = relationship(
    #     "Pago",
    #     back_populates="usuario"
    # )
    
    # Facturas - COMENTADO: modelo no implementado aún
    # facturas = relationship(
    #     "FacturaElectronica",
    #     back_populates="usuario"
    # )
    
    # Códigos de descuento - COMENTADO: modelo no implementado aún
    # codigos_descuento = relationship(
    #     "CodDescuento",
    #     back_populates="usuario"
    # )
    
    def __repr__(self):
        return f"<Usuario {self.nombre} {self.apellido} ({self.correo})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "rol": self.rol,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "correo": self.correo,
            "documento": self.documento,
            "telefono": self.telefono,
            "tipo_persona": self.tipo_persona,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            "estado": self.estado,
            "ranking": float(self.ranking) if self.ranking else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
