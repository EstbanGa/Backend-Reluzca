from typing import List, Optional
from fastapi import HTTPException, status
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.domain.schemas.plan import PlanCreate, PlanUpdate, PlanResponse


class PlanService:
    def __init__(self, plan_repository: PlanRepository):
        self.plan_repository = plan_repository

    def get_plan(self, plan_id: int) -> PlanResponse:
        """Obtiene un plan por ID"""
        plan = self.plan_repository.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        return PlanResponse.model_validate(plan)

    def get_planes(self, skip: int = 0, limit: int = 100, activo_only: bool = False) -> List[PlanResponse]:
        """Obtiene todos los planes"""
        planes = self.plan_repository.get_all(skip=skip, limit=limit, activo_only=activo_only)
        return [PlanResponse.model_validate(p) for p in planes]

    def search_planes(self, query: str, skip: int = 0, limit: int = 100) -> List[PlanResponse]:
        """Busca planes por nombre"""
        planes = self.plan_repository.search(query, skip=skip, limit=limit)
        return [PlanResponse.model_validate(p) for p in planes]

    def create_plan(self, plan_data: PlanCreate) -> PlanResponse:
        """Crea un nuevo plan"""
        # Verificar si ya existe un plan con el mismo nombre
        existing_plan = self.plan_repository.get_by_nombre(plan_data.nombre)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un plan con ese nombre"
            )

        # Crear plan
        plan = self.plan_repository.create(plan_data)
        return PlanResponse.model_validate(plan)

    def update_plan(self, plan_id: int, plan_data: PlanUpdate) -> PlanResponse:
        """Actualiza un plan existente"""
        # Verificar que el plan existe
        existing_plan = self.plan_repository.get_by_id(plan_id)
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )

        # Si se actualiza el nombre, verificar que no esté en uso
        if plan_data.nombre and plan_data.nombre != existing_plan.nombre:
            nombre_in_use = self.plan_repository.get_by_nombre(plan_data.nombre)
            if nombre_in_use:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un plan con ese nombre"
                )

        # Actualizar plan
        plan = self.plan_repository.update(plan_id, plan_data)
        return PlanResponse.model_validate(plan)

    def delete_plan(self, plan_id: int) -> dict:
        """Elimina un plan"""
        success = self.plan_repository.delete(plan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        return {"message": "Plan eliminado exitosamente"}

    def deactivate_plan(self, plan_id: int) -> PlanResponse:
        """Desactiva un plan"""
        plan = self.plan_repository.deactivate(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        return PlanResponse.model_validate(plan)
