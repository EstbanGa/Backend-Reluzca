"""
Actividad Service - Business logic for Actividad management.
"""
from typing import List
from uuid import UUID
from fastapi import HTTPException, status

from app.infrastructure.repositories.actividad_repository import ActividadRepository
from app.domain.schemas.actividad import ActividadCreate, ActividadUpdate, ActividadResponse


class ActividadService:
    def __init__(self, actividad_repository: ActividadRepository):
        self.actividad_repository = actividad_repository

    def get_actividad(self, actividad_id: UUID) -> ActividadResponse:
        """Obtiene una actividad por ID."""
        actividad = self.actividad_repository.get_by_id(actividad_id)
        if not actividad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada",
            )
        return ActividadResponse.model_validate(actividad)

    def get_actividades(self, skip: int = 0, limit: int = 100, activa_only: bool = False) -> List[ActividadResponse]:
        """Obtiene todas las actividades."""
        actividades = self.actividad_repository.get_all(skip=skip, limit=limit, activa_only=activa_only)
        return [ActividadResponse.model_validate(a) for a in actividades]

    def search_actividades(self, query: str, skip: int = 0, limit: int = 100) -> List[ActividadResponse]:
        """Busca actividades por nombre."""
        actividades = self.actividad_repository.search(query, skip=skip, limit=limit)
        return [ActividadResponse.model_validate(a) for a in actividades]

    def create_actividad(self, actividad_data: ActividadCreate) -> ActividadResponse:
        """Crea una nueva actividad."""
        existing = self.actividad_repository.get_by_nombre(actividad_data.nombre)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una actividad con ese nombre",
            )
        actividad = self.actividad_repository.create(actividad_data)
        return ActividadResponse.model_validate(actividad)

    def update_actividad(self, actividad_id: UUID, actividad_data: ActividadUpdate) -> ActividadResponse:
        """Actualiza una actividad existente."""
        existing = self.actividad_repository.get_by_id(actividad_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada",
            )

        if actividad_data.nombre and actividad_data.nombre != existing.nombre:
            nombre_en_uso = self.actividad_repository.get_by_nombre(actividad_data.nombre)
            if nombre_en_uso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una actividad con ese nombre",
                )

        actividad = self.actividad_repository.update(actividad_id, actividad_data)
        return ActividadResponse.model_validate(actividad)

    def delete_actividad(self, actividad_id: UUID) -> dict:
        """Elimina una actividad."""
        success = self.actividad_repository.delete(actividad_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada",
            )
        return {"message": "Actividad eliminada exitosamente"}
