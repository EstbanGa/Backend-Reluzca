from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID


class ReservaBase(BaseModel):
    """Schema base para Reserva con todos los campos de Django"""
    id_usuario: UUID
    id_empleada: Optional[UUID] = None
    id_plan: Optional[UUID] = None
    id_lugar: Optional[UUID] = None
    fecha: date
    hora_inicio: time
    hora_final: time
    estado: str = Field(default="pendiente", max_length=20)  # pendiente, confirmada, en_proceso, completada, cancelada
    estado_pago: str = Field(default="SIN_PAGAR", max_length=20)  # SIN_PAGAR, PAGADO, REEMBOLSADO
    descripcion: Optional[str] = None
    precio_total: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class ReservaCreate(ReservaBase):
    """Schema para crear reserva"""
    pass


class ReservaUpdate(BaseModel):
    """Schema para actualizar reserva - todos los campos opcionales"""
    id_empleada: Optional[UUID] = None
    id_plan: Optional[UUID] = None
    id_lugar: Optional[UUID] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_final: Optional[time] = None
    estado: Optional[str] = Field(None, max_length=20)
    estado_pago: Optional[str] = Field(None, max_length=20)
    descripcion: Optional[str] = None
    precio_total: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)


class ReservaResponse(BaseModel):
    """Schema de respuesta con TODOS los campos de Django"""
    id: UUID
    id_usuario: UUID
    id_empleada: Optional[UUID] = None
    id_plan: Optional[UUID] = None
    id_lugar: Optional[UUID] = None
    fecha: date
    hora_inicio: time
    hora_final: time
    estado: str
    estado_pago: str
    descripcion: Optional[str] = None
    precio_total: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReservasEstadisticas(BaseModel):
    """Schema para estadísticas de reservas"""
    total: int
    total_filtradas: int
    activas: int
    completadas: int
    canceladas: int
    pendientes: int


class ReservasPaginacion(BaseModel):
    """Schema para información de paginación"""
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None


class ReservasWithStatsResponse(BaseModel):
    """Schema de respuesta con reservas y estadísticas"""
    message: str
    reservas: List[dict]
    estadisticas: ReservasEstadisticas
    paginacion: ReservasPaginacion
