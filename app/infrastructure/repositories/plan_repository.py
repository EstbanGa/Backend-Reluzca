from sqlalchemy.orm import Session
from typing import List, Optional
from app.domain.models.plan import Plan
from app.domain.schemas.plan import PlanCreate, PlanUpdate


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, plan_id: int) -> Optional[Plan]:
        return self.db.query(Plan).filter(Plan.id == plan_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, activo_only: bool = False) -> List[Plan]:
        """Obtiene todos los planes (usa 'estado' en vez de 'activo')"""
        query = self.db.query(Plan)
        if activo_only:
            query = query.filter(Plan.estado == True)
        return query.offset(skip).limit(limit).all()

    def get_by_nombre(self, nombre: str) -> Optional[Plan]:
        return self.db.query(Plan).filter(Plan.nombre == nombre).first()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Plan]:
        search_filter = Plan.nombre.ilike(f"%{query}%")
        return self.db.query(Plan).filter(search_filter).offset(skip).limit(limit).all()

    def create(self, plan_data: PlanCreate) -> Plan:
        db_plan = Plan(**plan_data.model_dump())
        self.db.add(db_plan)
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

    def update(self, plan_id: int, plan_data: PlanUpdate) -> Optional[Plan]:
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return None

        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_plan, field, value)

        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

    def delete(self, plan_id: int) -> bool:
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return False

        self.db.delete(db_plan)
        self.db.commit()
        return True

    def deactivate(self, plan_id: int) -> Optional[Plan]:
        """Desactiva un plan (usa 'estado' en vez de 'activo')"""
        db_plan = self.get_by_id(plan_id)
        if not db_plan:
            return None

        db_plan.estado = False
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan

        db_plan.activo = False
        self.db.commit()
        self.db.refresh(db_plan)
        return db_plan
