"""
Calificacion API endpoints - FastAPI routes for Calificacion management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.calificacion_repository import CalificacionRepository
from app.services.calificacion_service import CalificacionService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])


# Pydantic schemas
class CalificacionCreate(BaseModel):
    id_reserva: str
    id_usuario: str
    id_empleada: Optional[str] = None
    calificacion_servicio: int  # 1-5
    calificacion_empleada: Optional[int] = None  # 1-5
    comentario: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/usuario/{usuario_id}")
def get_calificaciones_by_usuario(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all calificaciones for a specific user with statistics.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        calificacion_repository = CalificacionRepository(db)
        calificacion_service = CalificacionService(calificacion_repository)
        
        # Get calificaciones with statistics
        result = calificacion_service.get_calificaciones_by_usuario_with_stats(usuario_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener calificaciones: {str(e)}")


@router.post("/")
def create_calificacion(
    calificacion_data: CalificacionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new calificacion.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        calificacion_repository = CalificacionRepository(db)
        calificacion_service = CalificacionService(calificacion_repository)
        
        # Check if calificacion already exists for this reserva
        existing = calificacion_repository.get_by_reserva(calificacion_data.id_reserva)
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe una calificación para esta reserva")
        
        # Create calificacion
        result = calificacion_service.create_calificacion(calificacion_data.model_dump())
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear calificación: {str(e)}")


@router.get("/reservas-pendientes/{usuario_id}")
def get_reservas_pendientes_calificacion(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """
    Get reservas completadas que no han sido calificadas.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        from app.repositories.reserva_repository import ReservaRepository
        from app.models.reserva import Reserva
        
        # Create repositories
        reserva_repository = ReservaRepository(db)
        calificacion_repository = CalificacionRepository(db)
        
        # Get all completed reservas for the user
        reservas_completadas = reserva_repository.get_by_cliente_and_estado(usuario_id, "completada")
        
        # Filter out reservas that already have calificaciones
        reservas_pendientes = []
        for reserva in reservas_completadas:
            calificacion = calificacion_repository.get_by_reserva(str(reserva.id))
            if not calificacion:
                reservas_pendientes.append(reserva)
        
        # Format response
        result = []
        for reserva in reservas_pendientes:
            result.append({
                "id": str(reserva.id),
                "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
                "hora_inicio": str(reserva.hora_inicio) if reserva.hora_inicio else None,
                "hora_final": str(reserva.hora_final) if reserva.hora_final else None,
                "plan": {
                    "nombre": reserva.plan.nombre if reserva.plan else None
                } if reserva.plan else None,
                "empleada": {
                    "id": str(reserva.empleada.id) if reserva.empleada else None,
                    "nombre": reserva.empleada.nombre if reserva.empleada else None,
                    "apellido": reserva.empleada.apellido if reserva.empleada else None,
                } if reserva.empleada else None,
                "lugar": {
                    "nombre": reserva.lugar.nombre if reserva.lugar else None
                } if reserva.lugar else None
            })
        
        return {
            "message": "Reservas pendientes obtenidas exitosamente",
            "reservas": result,
            "total": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reservas pendientes: {str(e)}")


@router.delete("/{calificacion_id}")
def delete_calificacion(
    calificacion_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a calificacion by ID.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository
        calificacion_repository = CalificacionRepository(db)
        
        # Delete calificacion
        deleted = calificacion_repository.delete(calificacion_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Calificación no encontrada")
        
        return {"message": "Calificación eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar calificación: {str(e)}")
