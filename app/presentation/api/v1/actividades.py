"""
Actividades API endpoints - FastAPI routes for Actividad management.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.presentation.dependencies import get_db
from app.infrastructure.repositories.actividad_repository import ActividadRepository
from app.application.services.actividad_service import ActividadService
from app.domain.schemas.actividad import ActividadCreate, ActividadUpdate, ActividadResponse

router = APIRouter(prefix="/actividades", tags=["actividades"])


def get_actividad_service(db: Session = Depends(get_db)) -> ActividadService:
    """Inyección de dependencias para ActividadService."""
    actividad_repository = ActividadRepository(db)
    return ActividadService(actividad_repository)


@router.get("", response_model=List[ActividadResponse])
def get_actividades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activa_only: bool = Query(False),
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Obtiene todas las actividades (público)."""
    return actividad_service.get_actividades(skip=skip, limit=limit, activa_only=activa_only)


@router.get("/search", response_model=List[ActividadResponse])
def search_actividades(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Busca actividades por nombre (público)."""
    return actividad_service.search_actividades(q, skip=skip, limit=limit)


@router.get("/{actividad_id}", response_model=ActividadResponse)
def get_actividad(
    actividad_id: UUID,
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Obtiene una actividad por ID (público)."""
    return actividad_service.get_actividad(actividad_id)


@router.post("", response_model=ActividadResponse, status_code=status.HTTP_201_CREATED)
def create_actividad(
    actividad_data: ActividadCreate,
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Crea una nueva actividad (admin)."""
    return actividad_service.create_actividad(actividad_data)


@router.put("/{actividad_id}", response_model=ActividadResponse)
def update_actividad(
    actividad_id: UUID,
    actividad_data: ActividadUpdate,
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Actualiza una actividad existente (admin)."""
    return actividad_service.update_actividad(actividad_id, actividad_data)


@router.delete("/{actividad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_actividad(
    actividad_id: UUID,
    actividad_service: ActividadService = Depends(get_actividad_service),
):
    """Elimina una actividad (admin)."""
    actividad_service.delete_actividad(actividad_id)
