from sqlalchemy.orm import Session
from typing import List, Optional
from app.domain.models.ubicacion import UbicacionServicio
from app.domain.schemas.ubicacion import UbicacionServicioCreate, UbicacionServicioUpdate


class UbicacionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, ubicacion_id: str) -> Optional[UbicacionServicio]:
        return self.db.query(UbicacionServicio).filter(UbicacionServicio.id == ubicacion_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, activo_only: bool = False) -> List[UbicacionServicio]:
        """Obtiene todas las ubicaciones (usa 'estado' en vez de 'activo')"""
        query = self.db.query(UbicacionServicio)
        if activo_only:
            query = query.filter(UbicacionServicio.estado == True)
        return query.offset(skip).limit(limit).all()
    
    def get_by_usuario(self, usuario_id: str, skip: int = 0, limit: int = 100) -> List[UbicacionServicio]:
        """Obtiene ubicaciones por usuario"""
        return (
            self.db.query(UbicacionServicio)
            .filter(UbicacionServicio.id_usuario == usuario_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[UbicacionServicio]:
        """Busca ubicaciones por nombre o tipo"""
        from sqlalchemy import or_
        search_filter = or_(
            UbicacionServicio.nombre.ilike(f"%{query}%"),
            UbicacionServicio.nombre_lugar.ilike(f"%{query}%"),
            UbicacionServicio.tipo_lugar.ilike(f"%{query}%")
        )
        return self.db.query(UbicacionServicio).filter(search_filter).offset(skip).limit(limit).all()

    def create(self, ubicacion_data: UbicacionServicioCreate) -> UbicacionServicio:
        """Crea una nueva ubicación de servicio"""
        db_ubicacion = UbicacionServicio(**ubicacion_data.model_dump())
        self.db.add(db_ubicacion)
        self.db.commit()
        self.db.refresh(db_ubicacion)
        return db_ubicacion

    def update(self, ubicacion_id: str, ubicacion_data: UbicacionServicioUpdate) -> Optional[UbicacionServicio]:
        """Actualiza una ubicación"""
        db_ubicacion = self.get_by_id(ubicacion_id)
        if not db_ubicacion:
            return None

        update_data = ubicacion_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_ubicacion, field):
                setattr(db_ubicacion, field, value)

        self.db.commit()
        self.db.refresh(db_ubicacion)
        return db_ubicacion

    def delete(self, ubicacion_id: str) -> bool:
        db_ubicacion = self.get_by_id(ubicacion_id)
        if not db_ubicacion:
            return False

        self.db.delete(db_ubicacion)
        self.db.commit()
        return True

    def deactivate(self, ubicacion_id: str) -> Optional[UbicacionServicio]:
        """Desactiva una ubicación (usa 'estado' en vez de 'activo')"""
        db_ubicacion = self.get_by_id(ubicacion_id)
        if not db_ubicacion:
            return None

        db_ubicacion.estado = False
        self.db.commit()
        self.db.refresh(db_ubicacion)
        return db_ubicacion
