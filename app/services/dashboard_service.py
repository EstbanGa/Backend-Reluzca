"""Service para operaciones de dashboard"""
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime
from uuid import UUID

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Service para manejo de dashboard del cliente"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = DashboardRepository(db)
    
    def get_cliente_dashboard(self, usuario_id: UUID) -> Dict:
        """
        Obtiene toda la información del dashboard del cliente
        
        Args:
            usuario_id: UUID del usuario cliente
            
        Returns:
            Dict con toda la información del dashboard
        """
        # Información del cliente
        cliente_info = self.repository.get_cliente_info(usuario_id)
        if not cliente_info:
            raise ValueError("Cliente no encontrado")
        
        # Estadísticas de reservas
        estadisticas_reservas = self.repository.get_estadisticas_reservas(usuario_id)
        
        # Estadísticas de ubicaciones
        estadisticas_ubicaciones = self.repository.get_estadisticas_ubicaciones(usuario_id)
        
        # Datos principales
        datos_principales = {
            "reservas_recientes": self.repository.get_reservas_recientes(usuario_id),
            "proximas_reservas": self.repository.get_proximas_reservas(usuario_id),
            "empleadas_frecuentes": self.repository.get_empleadas_frecuentes(usuario_id),
            "ultimas_ubicaciones": self.repository.get_ultimas_ubicaciones(usuario_id),
            "descuentos_disponibles": self.repository.get_descuentos_disponibles(usuario_id),
            "planes_populares": self.repository.get_planes_populares()
        }
        
        # Información del sistema
        sistema = {
            "notificaciones_no_leidas": self.repository.get_notificaciones_no_leidas(usuario_id)
        }
        
        return {
            "message": "Dashboard del cliente obtenido exitosamente",
            "cliente_info": cliente_info,
            "estadisticas_reservas": estadisticas_reservas,
            "estadisticas_ubicaciones": estadisticas_ubicaciones,
            "datos_principales": datos_principales,
            "sistema": sistema,
            "fecha_consulta": datetime.now()
        }
