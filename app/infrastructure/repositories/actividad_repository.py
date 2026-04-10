"""
Actividad Repository - Data access layer for Actividad model.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.domain.models.actividad import Actividad
from app.domain.schemas.actividad import ActividadCreate, ActividadUpdate


class ActividadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, actividad_id: UUID) -> Optional[Actividad]:
        """Obtiene una actividad por ID."""
        return self.db.query(Actividad).filter(Actividad.id == actividad_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, activa_only: bool = False) -> List[Actividad]:
        """Obtiene todas las actividades."""
        query = self.db.query(Actividad)
        if activa_only:
            query = query.filter(Actividad.activa == True)
        return query.offset(skip).limit(limit).all()

    def get_by_nombre(self, nombre: str) -> Optional[Actividad]:
        """Busca una actividad por nombre exacto."""
        return self.db.query(Actividad).filter(Actividad.nombre == nombre).first()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Actividad]:
        """Busca actividades por nombre (búsqueda parcial)."""
        return (
            self.db.query(Actividad)
            .filter(Actividad.nombre.ilike(f"%{query}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, actividad_data: ActividadCreate) -> Actividad:
        """Crea una nueva actividad."""
        actividad = Actividad(**actividad_data.model_dump())
        self.db.add(actividad)
        self.db.commit()
        self.db.refresh(actividad)
        return actividad

    def update(self, actividad_id: UUID, actividad_data: ActividadUpdate) -> Optional[Actividad]:
        """Actualiza una actividad existente."""
        actividad = self.get_by_id(actividad_id)
        if not actividad:
            return None

        for field, value in actividad_data.model_dump(exclude_unset=True).items():
            setattr(actividad, field, value)

        self.db.commit()
        self.db.refresh(actividad)
        return actividad

    def delete(self, actividad_id: UUID) -> bool:
        """Elimina una actividad."""
        actividad = self.get_by_id(actividad_id)
        if not actividad:
            return False

        self.db.delete(actividad)
        self.db.commit()
        return True
