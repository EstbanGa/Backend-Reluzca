from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from app.domain.models.plan import Plan
from app.domain.schemas.plan import PlanCreate, PlanUpdate


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, plan_id: UUID) -> Optional[Plan]:
        return (
            self.db.query(Plan)
            .options(joinedload(Plan.actividades))
            .filter(Plan.id == plan_id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100, activo_only: bool = False) -> List[Plan]:
        """Obtiene todos los planes, incluyendo sus actividades asociadas."""
        query = self.db.query(Plan).options(joinedload(Plan.actividades))
        if activo_only:
            query = query.filter(Plan.estado == True)
        return query.offset(skip).limit(limit).all()

    def get_by_nombre(self, nombre: str) -> Optional[Plan]:
        return self.db.query(Plan).filter(Plan.nombre == nombre).first()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Plan]:
        search_filter = Plan.nombre.ilike(f"%{query}%")
        return (
            self.db.query(Plan)
            .options(joinedload(Plan.actividades))
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, plan_data: PlanCreate) -> Plan:
        db_plan = Plan(**plan_data.model_dump())
        self.db.add(db_plan)
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

    def update(self, plan_id: UUID, plan_data: PlanUpdate) -> Optional[Plan]:
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return None

        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan, field, value)

        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

    def delete(self, plan_id: UUID) -> bool:
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return False

        self.db.delete(db_plan)
        self.db.commit()
        return True

    def deactivate(self, plan_id: UUID) -> Optional[Plan]:
        """Desactiva un plan (estado = False)."""
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return None

        db_plan.estado = False
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan
