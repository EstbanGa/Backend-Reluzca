from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.dependencies import get_db
from app.repositories.notificacion_repository import NotificacionRepository
from app.services.notificacion_service import NotificacionService

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get("/cliente/{cliente_id}")
def get_notificaciones_by_cliente(
    cliente_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene notificaciones de un cliente con estadísticas
    SIN AUTENTICACIÓN - El frontend maneja la autenticación
    
    Retorna:
    - message: Mensaje de éxito
    - notificaciones: Lista de notificaciones con detalles de reserva
    - estadisticas: Estadísticas (total, leidas, no_leidas, por_tipo)
    """
    try:
        # Instanciar servicios manualmente
        notificacion_repository = NotificacionRepository(db)
        notificacion_service = NotificacionService(notificacion_repository)
        
        # Obtener notificaciones con estadísticas
        result = notificacion_service.get_notificaciones_by_cliente_with_stats(cliente_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener notificaciones: {str(e)}"
        )


@router.put("/{notificacion_id}/marcar-leida")
def mark_notificacion_as_read(
    notificacion_id: str,
    db: Session = Depends(get_db)
):
    """Marca una notificación como leída"""
    try:
        notificacion_repository = NotificacionRepository(db)
        notificacion_service = NotificacionService(notificacion_repository)
        
        result = notificacion_service.mark_as_read(notificacion_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar notificación como leída: {str(e)}"
        )


@router.put("/cliente/{cliente_id}/marcar-todas-leidas")
def mark_all_notificaciones_as_read(
    cliente_id: str,
    db: Session = Depends(get_db)
):
    """Marca todas las notificaciones de un cliente como leídas"""
    try:
        notificacion_repository = NotificacionRepository(db)
        notificacion_service = NotificacionService(notificacion_repository)
        
        result = notificacion_service.mark_all_as_read(cliente_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar todas las notificaciones como leídas: {str(e)}"
        )


@router.delete("/{notificacion_id}")
def delete_notificacion(
    notificacion_id: str,
    db: Session = Depends(get_db)
):
    """Elimina una notificación"""
    try:
        notificacion_repository = NotificacionRepository(db)
        notificacion_service = NotificacionService(notificacion_repository)
        
        result = notificacion_service.delete_notificacion(notificacion_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar notificación: {str(e)}"
        )
