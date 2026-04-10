"""
PQRS Repository - Data access layer for PQRS model.
"""
from sqlalchemy.orm import Session, joinedload
from app.domain.models.pqrs import PQRS
from typing import List, Optional


class PQRSRepository:
    """Repository for PQRS database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_usuario(self, usuario_id: str, skip: int = 0, limit: int = 100) -> List[PQRS]:
        """Get all PQRS created by a specific user with related data."""
        return (
            self.db.query(PQRS)
            .options(
                joinedload(PQRS.empleada),
                joinedload(PQRS.reserva)
            )
            .filter(PQRS.id_usuario == usuario_id)
            .order_by(PQRS.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_all(self, skip: int = 0, limit: int = 1000) -> List[PQRS]:
        """Get all PQRS with related data (for admin)."""
        return (
            self.db.query(PQRS)
            .options(
                joinedload(PQRS.usuario),
                joinedload(PQRS.empleada),
                joinedload(PQRS.reserva)
            )
            .order_by(PQRS.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_estado(self, usuario_id: str, estado: str) -> List[PQRS]:
        """Get PQRS by status for a specific user."""
        return (
            self.db.query(PQRS)
            .options(
                joinedload(PQRS.empleada),
                joinedload(PQRS.reserva)
            )
            .filter(PQRS.id_usuario == usuario_id, PQRS.estado == estado)
            .order_by(PQRS.created_at.desc())
            .all()
        )
    
    def get_by_tipo(self, usuario_id: str, tipo: str) -> List[PQRS]:
        """Get PQRS by type for a specific user."""
        return (
            self.db.query(PQRS)
            .options(
                joinedload(PQRS.empleada),
                joinedload(PQRS.reserva)
            )
            .filter(PQRS.id_usuario == usuario_id, PQRS.tipo == tipo)
            .order_by(PQRS.created_at.desc())
            .all()
        )
    
    def get_by_id(self, pqrs_id: str) -> Optional[PQRS]:
        """Get a specific PQRS by ID."""
        return (
            self.db.query(PQRS)
            .options(
                joinedload(PQRS.usuario),
                joinedload(PQRS.empleada),
                joinedload(PQRS.reserva)
            )
            .filter(PQRS.id == pqrs_id)
            .first()
        )
    
    def create(self, pqrs_data: dict) -> PQRS:
        """Create a new PQRS."""
        pqrs = PQRS(**pqrs_data)
        self.db.add(pqrs)
        self.db.commit()
        self.db.refresh(pqrs)
        return pqrs
    
    def update(self, pqrs_id: str, update_data: dict) -> Optional[PQRS]:
        """Update a PQRS by ID."""
        pqrs = self.db.query(PQRS).filter(PQRS.id == pqrs_id).first()
        if pqrs:
            for key, value in update_data.items():
                if hasattr(pqrs, key):
                    setattr(pqrs, key, value)
            self.db.commit()
            self.db.refresh(pqrs)
        return pqrs
    
    def delete(self, pqrs_id: str) -> bool:
        """Delete a PQRS by ID."""
        pqrs = self.db.query(PQRS).filter(PQRS.id == pqrs_id).first()
        if pqrs:
            self.db.delete(pqrs)
            self.db.commit()
            return True
        return False
