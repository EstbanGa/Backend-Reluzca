from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.reserva import Reserva
from app.schemas.reserva import ReservaCreate, ReservaUpdate


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, reserva_id: int) -> Optional[Reserva]:
        return self.db.query(Reserva).filter(Reserva.id == reserva_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Reserva]:
        return self.db.query(Reserva).offset(skip).limit(limit).all()

    def get_by_cliente(self, cliente_id: int, skip: int = 0, limit: int = 100) -> List[Reserva]:
        """Obtiene reservas por cliente (usa id_usuario)"""
        return (
            self.db.query(Reserva)
            .filter(Reserva.id_usuario == cliente_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_empleada(self, empleada_id: int, skip: int = 0, limit: int = 100) -> List[Reserva]:
        """Obtiene reservas por empleada (usa id_empleada)"""
        return (
            self.db.query(Reserva)
            .filter(Reserva.id_empleada == empleada_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_cliente_and_estado(self, cliente_id: str, estado: str, skip: int = 0, limit: int = 100) -> List[Reserva]:
        """Obtiene reservas por cliente y estado"""
        from sqlalchemy.orm import joinedload
        return (
            self.db.query(Reserva)
            .options(
                joinedload(Reserva.plan),
                joinedload(Reserva.empleada),
                joinedload(Reserva.lugar)
            )
            .filter(Reserva.id_usuario == cliente_id)
            .filter(Reserva.estado == estado)
            .order_by(Reserva.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_ubicacion(self, ubicacion_id: int, skip: int = 0, limit: int = 100) -> List[Reserva]:
        """Obtiene reservas por ubicación (usa id_lugar)"""
        return (
            self.db.query(Reserva)
            .filter(Reserva.id_lugar == ubicacion_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_estado(self, estado: str, skip: int = 0, limit: int = 100) -> List[Reserva]:
        return (
            self.db.query(Reserva)
            .filter(Reserva.estado == estado)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Reserva]:
        """Obtiene reservas por rango de fechas (usa campo 'fecha')"""
        return (
            self.db.query(Reserva)
            .filter(Reserva.fecha >= fecha_inicio.date() if hasattr(fecha_inicio, 'date') else fecha_inicio)
            .filter(Reserva.fecha <= fecha_fin.date() if hasattr(fecha_fin, 'date') else fecha_fin)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, reserva_data: ReservaCreate) -> Reserva:
        db_reserva = Reserva(**reserva_data.model_dump())
        self.db.add(db_reserva)
        self.db.commit()
        self.db.refresh(db_reserva)
        return db_reserva

    def update(self, reserva_id: int, reserva_data: ReservaUpdate) -> Optional[Reserva]:
        db_reserva = self.get_by_id(reserva_id)
        if not db_reserva:
            return None

        update_data = reserva_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_reserva, field, value)

        self.db.commit()
        self.db.refresh(db_reserva)
        return db_reserva

    def delete(self, reserva_id: int) -> bool:
        db_reserva = self.get_by_id(reserva_id)
        if not db_reserva:
            return False

        self.db.delete(db_reserva)
        self.db.commit()
        return True

    def cancel(self, reserva_id: int) -> Optional[Reserva]:
        db_reserva = self.get_by_id(reserva_id)
        if not db_reserva:
            return None

        db_reserva.estado = "cancelada"
        self.db.commit()
        self.db.refresh(db_reserva)
        return db_reserva
