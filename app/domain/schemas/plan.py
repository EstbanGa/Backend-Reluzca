from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID

from app.domain.schemas.actividad import ActividadResponse


class PlanBase(BaseModel):
    """Schema base para Plan."""
    nombre: str = Field(..., min_length=1, max_length=100)
    estado: bool = Field(default=True)
    tipo_plan: Optional[str] = Field(default="full", max_length=20)  # full, a_la_carte
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    horas_servicio: Optional[int] = None
    precio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class PlanCreate(PlanBase):
    """Schema para crear plan."""
    pass


class PlanUpdate(BaseModel):
    """Schema para actualizar plan — todos los campos opcionales."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    estado: Optional[bool] = None
    tipo_plan: Optional[str] = Field(None, max_length=20)
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    horas_servicio: Optional[int] = None
    precio: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class PlanResponse(BaseModel):
    """Schema de respuesta para Plan, incluyendo actividades asociadas."""
    id: UUID
    estado: bool
    nombre: str
    tipo_plan: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_final: Optional[date] = None
    descripcion: Optional[str] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    horas_servicio: Optional[int] = None
    precio: Optional[Decimal] = None
    actividades: List[ActividadResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
