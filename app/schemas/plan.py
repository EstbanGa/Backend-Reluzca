from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID


class PlanBase(BaseModel):
    """Schema base para Plan con todos los campos de Django"""
    nombre: str = Field(..., min_length=1, max_length=100)
    estado: bool = Field(default=True)
    servicios_asociados: Optional[List[str]] = Field(default_factory=list)
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None  # Hora en la que puede iniciar el servicio
    hora_final: Optional[time] = None  # Hora en la que puede finalizar el servicio
    horas_servicio: Optional[int] = None  # Horas de trabajo máximo
    precio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class PlanCreate(PlanBase):
    """Schema para crear plan"""
    pass


class PlanUpdate(BaseModel):
    """Schema para actualizar plan - todos los campos opcionales"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    estado: Optional[bool] = None
    servicios_asociados: Optional[List[str]] = None
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    horas_servicio: Optional[int] = None
    precio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class PlanResponse(BaseModel):
    """Schema de respuesta con TODOS los campos de Django"""
    id: UUID
    estado: bool
    nombre: str
    servicios_asociados: Optional[List[str]] = None
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    horas_servicio: Optional[int] = None
    precio: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
