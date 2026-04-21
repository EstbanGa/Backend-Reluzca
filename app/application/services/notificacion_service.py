from typing import List, Dict
from uuid import UUID
from app.infrastructure.repositories.notificacion_repository import NotificacionRepository
from app.domain.models.notificacion import NotificacionServicio


class NotificacionService:
    def __init__(self, notificacion_repository: NotificacionRepository):
        self.notificacion_repository = notificacion_repository

    def get_notificaciones_by_cliente_with_stats(self, cliente_id: UUID) -> Dict:
        """
        Obtiene notificaciones por cliente con estadísticas
        
        Retorna un dict con:
        - message: Mensaje de éxito
        - notificaciones: Lista de notificaciones con todos los detalles
        - estadisticas: Estadísticas de notificaciones
        """
        # Obtener todas las notificaciones del usuario
        notificaciones = self.notificacion_repository.get_by_usuario(cliente_id)

        # Calcular estadísticas
        total = len(notificaciones)
        leidas = len([n for n in notificaciones if n.leida])
        no_leidas = len([n for n in notificaciones if not n.leida])

        # Contar por tipo
        por_tipo = {}
        for notificacion in notificaciones:
            tipo = notificacion.tipo
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        # Convertir notificaciones a dict con detalles de reserva
        notificaciones_list = []
        for notificacion in notificaciones:
            notificacion_dict = {
                "id": str(notificacion.id),
                "id_reserva": str(notificacion.id_reserva) if notificacion.id_reserva else None,
                "id_usuario_destino": str(notificacion.id_usuario_destino),
                "tipo_notificacion": notificacion.tipo,
                "mensaje": notificacion.mensaje,
                "leida": notificacion.leida,
                "created_at": notificacion.created_at.isoformat() if notificacion.created_at else None,
            }
            
            # Agregar información de la reserva si existe
            if notificacion.reserva:
                notificacion_dict["reserva"] = {
                    "id": str(notificacion.reserva.id),
                    "fecha": notificacion.reserva.fecha.isoformat() if notificacion.reserva.fecha else None,
                    "hora_inicio": notificacion.reserva.hora_inicio.strftime('%H:%M:%S') if notificacion.reserva.hora_inicio else None,
                    "estado": notificacion.reserva.estado,
                }
                
                # Agregar info del plan si existe
                if notificacion.reserva.plan:
                    notificacion_dict["reserva"]["plan"] = {
                        "id": str(notificacion.reserva.plan.id),
                        "nombre": notificacion.reserva.plan.nombre,
                    }
                
                # Agregar info de la empleada si existe
                if notificacion.reserva.empleada:
                    notificacion_dict["reserva"]["empleada"] = {
                        "id": str(notificacion.reserva.empleada.id),
                        "nombre": notificacion.reserva.empleada.nombre,
                        "apellido": notificacion.reserva.empleada.apellido,
                    }
            
            notificaciones_list.append(notificacion_dict)
        
        return {
            "message": "Notificaciones obtenidas exitosamente",
            "notificaciones": notificaciones_list,
            "estadisticas": {
                "total": total,
                "leidas": leidas,
                "no_leidas": no_leidas,
                "por_tipo": por_tipo
            }
        }

    def mark_as_read(self, notificacion_id: UUID) -> Dict:
        """Marca una notificación como leída"""
        notificacion = self.notificacion_repository.mark_as_read(notificacion_id)
        if not notificacion:
            raise ValueError("Notificación no encontrada")
        
        return {
            "message": "Notificación marcada como leída",
            "notificacion": notificacion.to_dict()
        }

    def mark_all_as_read(self, cliente_id: UUID) -> Dict:
        """Marca todas las notificaciones de un cliente como leídas"""
        count = self.notificacion_repository.mark_all_as_read(cliente_id)
        
        return {
            "message": f"{count} notificaciones marcadas como leídas",
            "count": count
        }

    def delete_notificacion(self, notificacion_id: UUID) -> Dict:
        """Elimina una notificación"""
        success = self.notificacion_repository.delete(notificacion_id)
        if not success:
            raise ValueError("Notificación no encontrada")
        
        return {
            "message": "Notificación eliminada exitosamente"
        }
