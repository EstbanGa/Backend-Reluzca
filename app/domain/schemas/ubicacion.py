from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class UbicacionServicioBase(BaseModel):
    """Schema base para UbicacionServicio con todos los campos de Django"""
    id_usuario: UUID
    nombre: str = Field(..., min_length=1, max_length=100)
    tamaño: Optional[Dict[str, Any]] = None  # {"metros_cuadrados": 100, "tipo": "apartamento"}
    baños: Optional[int] = None
    pisos: Optional[int] = None
    ubicacion: Optional[Dict[str, Any]] = None  # {"lat": 4.123, "lng": -74.123, "direccion": "..."}
    nombre_lugar: Optional[str] = Field(None, max_length=100)
    tipo_lugar: Optional[str] = Field(None, max_length=20)  # casa, apartamento, oficina, etc
    estado: bool = Field(default=True)
    descripcion: Optional[str] = None


class UbicacionServicioCreate(UbicacionServicioBase):
    """Schema para crear ubicación de servicio"""
    pass


class UbicacionServicioUpdate(BaseModel):
    """Schema para actualizar ubicación - todos los campos opcionales"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    tamaño: Optional[Dict[str, Any]] = None
    baños: Optional[int] = None
    pisos: Optional[int] = None
    ubicacion: Optional[Dict[str, Any]] = None
    nombre_lugar: Optional[str] = Field(None, max_length=100)
    tipo_lugar: Optional[str] = Field(None, max_length=20)
    estado: Optional[bool] = None
    descripcion: Optional[str] = None


class UbicacionServicioResponse(BaseModel):
    """Schema de respuesta con TODOS los campos de Django"""
    id: UUID
    id_usuario: UUID
    nombre: str
    tamaño: Optional[Dict[str, Any]] = None
    baños: Optional[int] = None
    pisos: Optional[int] = None
    ubicacion: Optional[Dict[str, Any]] = None
    nombre_lugar: Optional[str] = None
    tipo_lugar: Optional[str] = None
    estado: bool
    descripcion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UbicacionesEmpleadaBase(BaseModel):
    """Schema base para UbicacionesEmpleada con todos los campos de Django"""
    id_empleada: UUID
    id_reserva: Optional[UUID] = None
    fecha_hora: Optional[datetime] = None
    coordenadas: Dict[str, Any]  # {"lat": 4.123, "lng": -74.123}
    tipo_evento: Optional[str] = Field(None, max_length=20)  # inicio, en_camino, llegada, fin
    distancia_destino_metros: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    estado: Optional[str] = Field(None, max_length=20)
    precision_metros: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)


class UbicacionesEmpleadaCreate(UbicacionesEmpleadaBase):
    """Schema para crear ubicación de empleada"""
    pass


class UbicacionesEmpleadaUpdate(BaseModel):
    """Schema para actualizar ubicación de empleada - todos los campos opcionales"""
    id_reserva: Optional[UUID] = None
    fecha_hora: Optional[datetime] = None
    coordenadas: Optional[Dict[str, Any]] = None
    tipo_evento: Optional[str] = Field(None, max_length=20)
    distancia_destino_metros: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    estado: Optional[str] = Field(None, max_length=20)
    precision_metros: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)


class UbicacionesEmpleadaResponse(BaseModel):
    """Schema de respuesta con TODOS los campos de Django"""
    id: UUID
    id_empleada: UUID
    id_reserva: Optional[UUID] = None
    fecha_hora: Optional[datetime] = None
    coordenadas: Dict[str, Any]
    tipo_evento: Optional[str] = None
    distancia_destino_metros: Optional[Decimal] = None
    estado: Optional[str] = None
    precision_metros: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
