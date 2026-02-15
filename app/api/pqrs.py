"""
PQRS API endpoints - FastAPI routes for PQRS management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.pqrs_repository import PQRSRepository
from app.services.pqrs_service import PQRSService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/pqrs", tags=["PQRS"])


# Pydantic schemas
class PQRSCreate(BaseModel):
    id_usuario: str
    id_reserva: Optional[str] = None
    tipo: str  # peticion, queja, reclamo, sugerencia
    descripcion: str
    prioridad: Optional[str] = "media"  # baja, media, alta


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/usuario/{usuario_id}")
def get_pqrs_by_usuario(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all PQRS for a specific user with statistics.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        pqrs_repository = PQRSRepository(db)
        pqrs_service = PQRSService(pqrs_repository)
        
        # Get PQRS with statistics
        result = pqrs_service.get_pqrs_by_usuario_with_stats(usuario_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener PQRS: {str(e)}")


@router.post("/")
def create_pqrs(
    pqrs_data: PQRSCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new PQRS.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        pqrs_repository = PQRSRepository(db)
        pqrs_service = PQRSService(pqrs_repository)
        
        # Create PQRS
        result = pqrs_service.create_pqrs(pqrs_data.model_dump())
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear PQRS: {str(e)}")


@router.get("/admin/all")
def get_all_pqrs_admin(
    db: Session = Depends(get_db)
):
    """
    Get all PQRS for admin with statistics.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        pqrs_repository = PQRSRepository(db)
        pqrs_service = PQRSService(pqrs_repository)
        
        # Get all PQRS with statistics
        result = pqrs_service.get_all_pqrs_with_stats()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener PQRS: {str(e)}")


class PQRSRespuesta(BaseModel):
    respuesta: str
    estado: Optional[str] = "resuelto"
    id_empleada: str


@router.put("/{pqrs_id}/responder")
def responder_pqrs(
    pqrs_id: str,
    respuesta_data: PQRSRespuesta,
    db: Session = Depends(get_db)
):
    """
    Respond to a PQRS and update its status.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository and service
        pqrs_repository = PQRSRepository(db)
        pqrs_service = PQRSService(pqrs_repository)
        
        # Respond to PQRS
        result = pqrs_service.responder_pqrs(pqrs_id, respuesta_data.model_dump())
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al responder PQRS: {str(e)}")


@router.delete("/{pqrs_id}")
def delete_pqrs(
    pqrs_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a PQRS by ID.
    NO AUTHENTICATION - Frontend handles auth via localStorage.
    """
    try:
        # Create repository
        pqrs_repository = PQRSRepository(db)
        
        # Delete PQRS
        deleted = pqrs_repository.delete(pqrs_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="PQRS no encontrado")
        
        return {"message": "PQRS eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar PQRS: {str(e)}")
