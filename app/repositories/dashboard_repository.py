"""Repository para operaciones de dashboard"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta
from uuid import UUID

from app.models.usuario import Usuario
from app.models.reserva import Reserva
from app.models.ubicacion import UbicacionServicio
from app.models.plan import Plan


class DashboardRepository:
    """Repository para datos de dashboard del cliente"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_cliente_info(self, usuario_id: UUID) -> Dict:
        """Obtiene información básica del cliente"""
        usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
            
        return {
            "nombre": usuario.nombre or "",
            "apellido": usuario.apellido or "",
            "correo": usuario.correo or "",
            "telefono": usuario.telefono or "",
            "fecha_registro": usuario.created_at
        }
    
    def get_estadisticas_reservas(self, usuario_id: UUID) -> Dict:
        """Obtiene estadísticas de reservas del cliente"""
        # Total de reservas
        total = self.db.query(func.count(Reserva.id)).filter(
            Reserva.id_usuario == usuario_id
        ).scalar() or 0
        
        # Reservas por estado
        activas = self.db.query(func.count(Reserva.id)).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.estado.in_(["confirmada", "en_proceso"])
        ).scalar() or 0
        
        completadas = self.db.query(func.count(Reserva.id)).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.estado == "completada"
        ).scalar() or 0
        
        canceladas = self.db.query(func.count(Reserva.id)).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.estado == "cancelada"
        ).scalar() or 0
        
        pendientes = self.db.query(func.count(Reserva.id)).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.estado == "pendiente"
        ).scalar() or 0
        
        # Reservas por estado (para gráficos)
        reservas_por_estado = []
        estados = ["pendiente", "confirmada", "en_proceso", "completada", "cancelada"]
        for estado in estados:
            count = self.db.query(func.count(Reserva.id)).filter(
                Reserva.id_usuario == usuario_id,
                Reserva.estado == estado
            ).scalar() or 0
            if count > 0:
                reservas_por_estado.append({"estado": estado, "count": count})
        
        return {
            "total_reservas": total,
            "reservas_activas": activas,
            "reservas_completadas": completadas,
            "reservas_canceladas": canceladas,
            "reservas_pendientes": pendientes,
            "reservas_por_estado": reservas_por_estado
        }
    
    def get_estadisticas_ubicaciones(self, usuario_id: UUID) -> Dict:
        """Obtiene estadísticas de ubicaciones del cliente"""
        total = self.db.query(func.count(UbicacionServicio.id)).filter(
            UbicacionServicio.id_usuario == usuario_id
        ).scalar() or 0
        
        activas = self.db.query(func.count(UbicacionServicio.id)).filter(
            UbicacionServicio.id_usuario == usuario_id,
            UbicacionServicio.estado == True
        ).scalar() or 0
        
        return {
            "total_ubicaciones": total,
            "ubicaciones_activas": activas
        }
    
    def get_reservas_recientes(self, usuario_id: UUID, limit: int = 5) -> List[Dict]:
        """Obtiene las reservas más recientes del cliente"""
        reservas = self.db.query(Reserva).filter(
            Reserva.id_usuario == usuario_id
        ).order_by(desc(Reserva.created_at)).limit(limit).all()
        
        result = []
        for reserva in reservas:
            result.append({
                "id": str(reserva.id),
                "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
                "hora_inicio": reserva.hora_inicio.isoformat() if reserva.hora_inicio else None,
                "hora_final": reserva.hora_final.isoformat() if reserva.hora_final else None,
                "estado": reserva.estado,
                "precio_total": float(reserva.precio_total) if reserva.precio_total else 0,
                "ubicacion": reserva.lugar.nombre if reserva.lugar else None,
                "empleada": f"{reserva.empleada.nombre} {reserva.empleada.apellido}" if reserva.empleada else None
            })
        
        return result
    
    def get_proximas_reservas(self, usuario_id: UUID, limit: int = 5) -> List[Dict]:
        """Obtiene las próximas reservas del cliente"""
        hoy = datetime.now().date()
        
        reservas = self.db.query(Reserva).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.fecha >= hoy,
            Reserva.estado.in_(["pendiente", "confirmada"])
        ).order_by(Reserva.fecha, Reserva.hora_inicio).limit(limit).all()
        
        result = []
        for reserva in reservas:
            result.append({
                "id": str(reserva.id),
                "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
                "hora_inicio": reserva.hora_inicio.isoformat() if reserva.hora_inicio else None,
                "hora_final": reserva.hora_final.isoformat() if reserva.hora_final else None,
                "estado": reserva.estado,
                "precio_total": float(reserva.precio_total) if reserva.precio_total else 0,
                "ubicacion": reserva.lugar.nombre if reserva.lugar else None,
                "empleada": f"{reserva.empleada.nombre} {reserva.empleada.apellido}" if reserva.empleada else None
            })
        
        return result
    
    def get_empleadas_frecuentes(self, usuario_id: UUID, limit: int = 5) -> List[Dict]:
        """Obtiene las empleadas más frecuentes del cliente"""
        # Agrupa por empleada y cuenta reservas
        empleadas = self.db.query(
            Usuario.id,
            Usuario.nombre,
            Usuario.apellido,
            Usuario.correo,
            func.count(Reserva.id).label('total_reservas')
        ).join(
            Reserva, Reserva.id_empleada == Usuario.id
        ).filter(
            Reserva.id_usuario == usuario_id,
            Reserva.id_empleada.isnot(None)
        ).group_by(
            Usuario.id, Usuario.nombre, Usuario.apellido, Usuario.correo
        ).order_by(
            desc('total_reservas')
        ).limit(limit).all()
        
        result = []
        for empleada in empleadas:
            result.append({
                "id": str(empleada.id),
                "nombre": empleada.nombre,
                "apellido": empleada.apellido,
                "correo": empleada.correo,
                "total_reservas": empleada.total_reservas
            })
        
        return result
    
    def get_ultimas_ubicaciones(self, usuario_id: UUID, limit: int = 5) -> List[Dict]:
        """Obtiene las últimas ubicaciones creadas por el cliente"""
        ubicaciones = self.db.query(UbicacionServicio).filter(
            UbicacionServicio.id_usuario == usuario_id
        ).order_by(desc(UbicacionServicio.created_at)).limit(limit).all()
        
        result = []
        for ubicacion in ubicaciones:
            result.append({
                "id": str(ubicacion.id),
                "nombre": ubicacion.nombre,
                "tipo_lugar": ubicacion.tipo_lugar,
                "estado": ubicacion.estado,
                "created_at": ubicacion.created_at.isoformat() if ubicacion.created_at else None
            })
        
        return result
    
    def get_descuentos_disponibles(self, usuario_id: UUID) -> List[Dict]:
        """Obtiene descuentos disponibles para el cliente"""
        # Por ahora retornamos lista vacía
        # TODO: Implementar cuando exista el modelo de descuentos/cupones
        return []
    
    def get_planes_populares(self, limit: int = 6) -> List[Dict]:
        """Obtiene los planes más populares"""
        # Obtiene planes más usados
        planes = self.db.query(
            Plan.id,
            Plan.nombre,
            Plan.precio,
            Plan.descripcion,
            func.count(Reserva.id).label('total_reservas')
        ).outerjoin(
            Reserva, Reserva.id_plan == Plan.id
        ).group_by(
            Plan.id, Plan.nombre, Plan.precio, Plan.descripcion
        ).order_by(
            desc('total_reservas')
        ).limit(limit).all()
        
        result = []
        for plan in planes:
            result.append({
                "id": str(plan.id),
                "nombre": plan.nombre,
                "precio": float(plan.precio) if plan.precio else 0,
                "descripcion": plan.descripcion,
                "total_reservas": plan.total_reservas
            })
        
        return result
    
    def get_notificaciones_no_leidas(self, usuario_id: UUID) -> int:
        """Obtiene el número de notificaciones no leídas"""
        # Por ahora retornamos 0
        # TODO: Implementar cuando exista el modelo de notificaciones
        return 0
