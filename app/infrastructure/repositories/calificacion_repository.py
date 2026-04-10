"""
Calificacion Repository - Data access layer for Calificacion model.
"""
from sqlalchemy.orm import Session, joinedload
from app.domain.models.calificacion import Calificacion
from app.domain.models.reserva import Reserva
from typing import List, Optional


class CalificacionRepository:
    """Repository for Calificacion database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_usuario(self, usuario_id: str, skip: int = 0, limit: int = 100) -> List[Calificacion]:
        """Get all calificaciones created by a specific user with related data."""
        return (
            self.db.query(Calificacion)
            .options(
                joinedload(Calificacion.reserva).joinedload(Reserva.plan),
                joinedload(Calificacion.reserva).joinedload(Reserva.empleada),
                joinedload(Calificacion.empleada)
            )
            .filter(Calificacion.id_usuario == usuario_id)
            .order_by(Calificacion.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_reserva(self, reserva_id: str) -> Optional[Calificacion]:
        """Get calificacion for a specific reserva."""
        return (
            self.db.query(Calificacion)
            .filter(Calificacion.id_reserva == reserva_id)
            .first()
        )
    
    def create(self, calificacion_data: dict) -> Calificacion:
        """Create a new calificacion."""
        calificacion = Calificacion(**calificacion_data)
        self.db.add(calificacion)
        self.db.commit()
        self.db.refresh(calificacion)
        return calificacion
    
    def update(self, calificacion_id: str, calificacion_data: dict) -> Optional[Calificacion]:
        """Update an existing calificacion."""
        calificacion = self.db.query(Calificacion).filter(Calificacion.id == calificacion_id).first()
        if calificacion:
            for key, value in calificacion_data.items():
                setattr(calificacion, key, value)
            self.db.commit()
            self.db.refresh(calificacion)
        return calificacion
    
    def delete(self, calificacion_id: str) -> bool:
        """Delete a calificacion by ID."""
        calificacion = self.db.query(Calificacion).filter(Calificacion.id == calificacion_id).first()
        if calificacion:
            self.db.delete(calificacion)
            self.db.commit()
            return True
        return False
