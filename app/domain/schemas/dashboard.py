"""Schemas para endpoints de dashboard"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


class EstadisticasReservasCliente(BaseModel):
    """Estadísticas de reservas del cliente"""
    total_reservas: int
    reservas_activas: int
    reservas_completadas: int
    reservas_canceladas: int
    reservas_pendientes: int
    reservas_por_estado: List[dict]  # [{"estado": "pendiente", "count": 5}]


class EstadisticasUbicacionesCliente(BaseModel):
    """Estadísticas de ubicaciones del cliente"""
    total_ubicaciones: int
    ubicaciones_activas: int


class DatosPrincipalesCliente(BaseModel):
    """Datos principales para el dashboard del cliente"""
    reservas_recientes: List[dict]
    proximas_reservas: List[dict]
    empleadas_frecuentes: List[dict]
    ultimas_ubicaciones: List[dict]
    descuentos_disponibles: List[dict]
    planes_populares: List[dict]


class SistemaInfo(BaseModel):
    """Información del sistema"""
    notificaciones_no_leidas: int


class ClienteInfo(BaseModel):
    """Información básica del cliente"""
    nombre: str
    apellido: str
    correo: str
    telefono: str
    fecha_registro: Optional[datetime] = None


class ClienteDashboardResponse(BaseModel):
    """Respuesta completa del dashboard del cliente"""
    message: str
    cliente_info: ClienteInfo
    estadisticas_reservas: EstadisticasReservasCliente
    estadisticas_ubicaciones: EstadisticasUbicacionesCliente
    datos_principales: DatosPrincipalesCliente
    sistema: SistemaInfo
    fecha_consulta: datetime
