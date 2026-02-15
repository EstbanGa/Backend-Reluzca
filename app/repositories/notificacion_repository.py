from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models.notificacion import NotificacionServicio


class NotificacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, notificacion_id: UUID) -> Optional[NotificacionServicio]:
        return self.db.query(NotificacionServicio).filter(NotificacionServicio.id == notificacion_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[NotificacionServicio]:
        return self.db.query(NotificacionServicio).offset(skip).limit(limit).all()

    def get_by_cliente(self, cliente_id: UUID, skip: int = 0, limit: int = 100) -> List[NotificacionServicio]:
        """Obtiene notificaciones por cliente con ordenamiento por fecha"""
        return (
            self.db.query(NotificacionServicio)
            .filter(NotificacionServicio.id_cliente == cliente_id)
            .order_by(NotificacionServicio.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread_by_cliente(self, cliente_id: UUID) -> List[NotificacionServicio]:
        """Obtiene notificaciones no leídas por cliente"""
        return (
            self.db.query(NotificacionServicio)
            .filter(
                NotificacionServicio.id_cliente == cliente_id,
                NotificacionServicio.leida == False
            )
            .order_by(NotificacionServicio.created_at.desc())
            .all()
        )

    def mark_as_read(self, notificacion_id: UUID) -> Optional[NotificacionServicio]:
        """Marca una notificación como leída"""
        notificacion = self.get_by_id(notificacion_id)
        if notificacion:
            notificacion.leida = True
            self.db.commit()
            self.db.refresh(notificacion)
        return notificacion

    def mark_all_as_read(self, cliente_id: UUID) -> int:
        """Marca todas las notificaciones de un cliente como leídas"""
        count = (
            self.db.query(NotificacionServicio)
            .filter(
                NotificacionServicio.id_cliente == cliente_id,
                NotificacionServicio.leida == False
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
