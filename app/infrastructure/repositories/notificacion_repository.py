from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.domain.models.notificacion import NotificacionServicio


class NotificacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, notificacion_id: UUID) -> Optional[NotificacionServicio]:
        return self.db.query(NotificacionServicio).filter(NotificacionServicio.id == notificacion_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[NotificacionServicio]:
        return self.db.query(NotificacionServicio).offset(skip).limit(limit).all()

    def get_by_usuario(self, usuario_id: UUID, skip: int = 0, limit: int = 100) -> List[NotificacionServicio]:
        """Obtiene notificaciones por usuario destino con ordenamiento por fecha."""
        return (
            self.db.query(NotificacionServicio)
            .filter(NotificacionServicio.id_usuario_destino == usuario_id)
            .order_by(NotificacionServicio.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread_by_usuario(self, usuario_id: UUID) -> List[NotificacionServicio]:
        """Obtiene notificaciones no leídas por usuario destino."""
        return (
            self.db.query(NotificacionServicio)
            .filter(
                NotificacionServicio.id_usuario_destino == usuario_id,
                NotificacionServicio.leida == False,
            )
            .order_by(NotificacionServicio.created_at.desc())
            .all()
        )

    def mark_as_read(self, notificacion_id: UUID) -> Optional[NotificacionServicio]:
        """Marca una notificación como leída."""
        notificacion = self.get_by_id(notificacion_id)
        if notificacion:
            notificacion.leida = True
            self.db.commit()
            self.db.refresh(notificacion)
        return notificacion

    def mark_all_as_read(self, usuario_id: UUID) -> int:
        """Marca todas las notificaciones de un usuario como leídas."""
        count = (
            self.db.query(NotificacionServicio)
            .filter(
                NotificacionServicio.id_usuario_destino == usuario_id,
                NotificacionServicio.leida == False,
            )
            .update({"leida": True})
        )
        self.db.commit()
        return count

    def delete(self, notificacion_id: UUID) -> bool:
        """Elimina una notificación"""
        notificacion = self.get_by_id(notificacion_id)
        if notificacion:
            self.db.delete(notificacion)
            self.db.commit()
            return True
        return False

    def create(
        self,
        id_usuario_destino: UUID,
        tipo: str,
        mensaje: str,
        canal: str = "in_app",
        id_reserva: Optional[UUID] = None,
        id_pqrs: Optional[UUID] = None,
    ) -> NotificacionServicio:
        """Crea una nueva notificación."""
        notif = NotificacionServicio(
            id_usuario_destino=id_usuario_destino,
            tipo=tipo,
            mensaje=mensaje,
            canal=canal,
            id_reserva=id_reserva,
            id_pqrs=id_pqrs,
            leida=False,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def get_all_with_details(self, skip: int = 0, limit: int = 100) -> List[NotificacionServicio]:
        """Obtiene todas las notificaciones con ordenamiento por fecha (admin)."""
        return (
            self.db.query(NotificacionServicio)
            .order_by(NotificacionServicio.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
