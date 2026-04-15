"""
PQRS API endpoints - FastAPI routes for PQRS management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.infrastructure.database import get_db
from app.infrastructure.repositories.pqrs_repository import PQRSRepository
from app.infrastructure.repositories.notificacion_repository import NotificacionRepository
from app.application.services.pqrs_service import PQRSService
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
    respondida_por: str


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
        
        # Responder PQRS
        result = pqrs_service.responder_pqrs(pqrs_id, respuesta_data.model_dump())

        # Crear notificación al usuario
        try:
            pqrs_obj = PQRSRepository(db).get_by_id(pqrs_id)
            if pqrs_obj:
                estado_final = respuesta_data.estado or "resuelto"
                if estado_final == "resuelto":
                    truncated = respuesta_data.respuesta[:120]
                    suffix = "..." if len(respuesta_data.respuesta) > 120 else ""
                    msg = f"Tu PQRS ha recibido una respuesta: {truncated}{suffix}"
                elif estado_final == "cerrado":
                    msg = "Tu PQRS ha sido respondida y cerrada por el equipo de Reluzca."
                elif estado_final == "en_proceso":
                    msg = "Tu PQRS está siendo atendida. Pronto recibirás una respuesta."
                else:
                    msg = f"El estado de tu PQRS ha sido actualizado a: {estado_final}."
                NotificacionRepository(db).create(
                    id_usuario_destino=UUID(str(pqrs_obj.id_usuario)),
                    tipo="pqrs",
                    mensaje=msg,
                    canal="in_app",
                    id_pqrs=UUID(str(pqrs_obj.id)),
                )
        except Exception:
            pass  # No fallar si la notificación falla

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


class PQRSCambioEstado(BaseModel):
    estado: str  # en_proceso, resuelto, cerrado, pendiente


@router.patch("/{pqrs_id}/estado")
def cambiar_estado_pqrs(
    pqrs_id: str,
    data: PQRSCambioEstado,
    db: Session = Depends(get_db),
):
    """Cambia solo el estado de un PQRS y notifica al usuario."""
    try:
        pqrs_repo = PQRSRepository(db)
        pqrs = pqrs_repo.get_by_id(pqrs_id)
        if not pqrs:
            raise HTTPException(status_code=404, detail="PQRS no encontrado")

        updated = pqrs_repo.update(pqrs_id, {
            "estado": data.estado,
            "updated_at": datetime.utcnow(),
        })

        # Notificar al usuario
        try:
            msgs = {
                "en_proceso": "Tu solicitud PQRS está siendo revisada y procesada por nuestro equipo.",
                "resuelto": "Tu solicitud PQRS ha sido marcada como resuelta.",
                "cerrado": "Tu solicitud PQRS ha sido cerrada.",
                "pendiente": "Tu solicitud PQRS ha vuelto a estado pendiente.",
            }
            msg = msgs.get(data.estado, f"El estado de tu PQRS fue actualizado a: {data.estado}.")
            NotificacionRepository(db).create(
                id_usuario_destino=UUID(str(pqrs.id_usuario)),
                tipo="pqrs",
                mensaje=msg,
                canal="in_app",
                id_pqrs=UUID(str(pqrs.id)),
            )
        except Exception:
            pass

        return {"message": "Estado actualizado correctamente", "pqrs": updated.to_dict() if updated else None}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar estado: {str(e)}")
