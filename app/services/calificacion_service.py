"""
Calificacion Service - Business logic for Calificacion management.
"""
from app.repositories.calificacion_repository import CalificacionRepository
from typing import Dict, Any, List
from datetime import datetime


class CalificacionService:
    """Service for Calificacion business logic."""
    
    def __init__(self, calificacion_repository: CalificacionRepository):
        self.calificacion_repository = calificacion_repository
    
    def get_calificaciones_by_usuario_with_stats(self, usuario_id: str) -> Dict[str, Any]:
        """Get all calificaciones for a user with statistics."""
        calificaciones_list = self.calificacion_repository.get_by_usuario(usuario_id)
        
        # Calculate statistics
        total = len(calificaciones_list)
        promedio_servicio = 0
        promedio_empleada = 0
        
        if total > 0:
            promedio_servicio = sum(c.calificacion_servicio for c in calificaciones_list) / total
            calificaciones_con_empleada = [c for c in calificaciones_list if c.calificacion_empleada is not None]
            if calificaciones_con_empleada:
                promedio_empleada = sum(c.calificacion_empleada for c in calificaciones_con_empleada) / len(calificaciones_con_empleada)
        
        # Count by rating
        por_calificacion_servicio = {}
        for cal in calificaciones_list:
            rating = cal.calificacion_servicio
            por_calificacion_servicio[rating] = por_calificacion_servicio.get(rating, 0) + 1
        
        # Format calificaciones data
        calificaciones_formatted = []
        for cal in calificaciones_list:
            cal_data = {
                "id": str(cal.id),
                "calificacion_servicio": cal.calificacion_servicio,
                "calificacion_empleada": cal.calificacion_empleada,
                "comentario": cal.comentario,
                "created_at": cal.created_at.isoformat() if cal.created_at else None,
            }
            
            # Add reserva info
            if cal.reserva:
                cal_data["reserva"] = {
                    "id": str(cal.reserva.id),
                    "fecha": cal.reserva.fecha.isoformat() if cal.reserva.fecha else None,
                    "plan": {
                        "nombre": cal.reserva.plan.nombre if cal.reserva.plan else None
                    } if cal.reserva.plan else None,
                    "empleada": {
                        "nombre": cal.reserva.empleada.nombre if cal.reserva.empleada else None,
                        "apellido": cal.reserva.empleada.apellido if cal.reserva.empleada else None,
                    } if cal.reserva.empleada else None
                }
            else:
                cal_data["reserva"] = None
            
            calificaciones_formatted.append(cal_data)
        
        return {
            "message": "Calificaciones obtenidas exitosamente",
            "calificaciones": calificaciones_formatted,
            "estadisticas": {
                "total": total,
                "promedio_servicio": round(promedio_servicio, 2),
                "promedio_empleada": round(promedio_empleada, 2),
                "por_calificacion": por_calificacion_servicio,
            }
        }
    
    def create_calificacion(self, calificacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calificacion."""
        # Set default values
        calificacion_data.setdefault("created_at", datetime.utcnow())
        calificacion_data.setdefault("updated_at", datetime.utcnow())
        
        calificacion = self.calificacion_repository.create(calificacion_data)
        
        return {
            "message": "Calificación creada exitosamente",
            "calificacion": calificacion.to_dict()
        }
