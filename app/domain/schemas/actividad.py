"""
Actividad schemas - Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ActividadBase(BaseModel):
    """Schema base para Actividad."""
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None
    precio_unitario: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    duracion_estimada_minutos: Optional[int] = None
    activa: bool = Field(default=True)


class ActividadCreate(ActividadBase):
    """Schema para crear una actividad."""
    pass


class ActividadUpdate(BaseModel):
    """Schema para actualizar una actividad — todos los campos opcionales."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = None
    precio_unitario: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    duracion_estimada_minutos: Optional[int] = None
    activa: Optional[bool] = None


class ActividadResponse(ActividadBase):
    """Schema de respuesta para Actividad."""
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
