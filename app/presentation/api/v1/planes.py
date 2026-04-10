from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.presentation.dependencies import get_db, get_current_user, require_role
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.application.services.plan_service import PlanService
from app.domain.schemas.plan import PlanCreate, PlanUpdate, PlanResponse
from app.domain.models.usuario import Usuario

router = APIRouter(prefix="/planes", tags=["planes"])


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    """Inyección de dependencias para PlanService"""
    plan_repository = PlanRepository(db)
    return PlanService(plan_repository)


@router.get("", response_model=List[PlanResponse])
def get_planes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activo_only: bool = Query(False),
    plan_service: PlanService = Depends(get_plan_service)
):
    """Obtiene todos los planes (público)"""
    return plan_service.get_planes(skip=skip, limit=limit, activo_only=activo_only)


@router.get("/search", response_model=List[PlanResponse])
def search_planes(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    plan_service: PlanService = Depends(get_plan_service)
):
    """Busca planes por nombre (público)"""
    return plan_service.search_planes(q, skip=skip, limit=limit)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: UUID,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Obtiene un plan por ID (público)"""
    return plan_service.get_plan(plan_id)


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Crea un nuevo plan"""
    return plan_service.create_plan(plan_data)


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    plan_data: PlanUpdate,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Actualiza un plan"""
    return plan_service.update_plan(plan_id, plan_data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Elimina un plan"""
    plan_service.delete_plan(plan_id)


@router.patch("/{plan_id}/deactivate", response_model=PlanResponse)
async def deactivate_plan(
    plan_id: UUID,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Desactiva un plan"""
    return plan_service.deactivate_plan(plan_id)
