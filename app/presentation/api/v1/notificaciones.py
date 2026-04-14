from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.presentation.dependencies import get_db
from app.infrastructure.repositories.notificacion_repository import NotificacionRepository
from app.application.services.notificacion_service import NotificacionService

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


class EnviarNotificacionRequest(BaseModel):
    mensaje: str
    tipo: str = "manual"  # sistema, manual, recordatorio, confirmacion, pago, pqrs
    canal: str = "in_app"  # in_app, email, ambos
    destinatario_tipo: str  # "usuario" | "rol"
    destinatario_id: Optional[str] = None   # UUID del usuario si destinatario_tipo=="usuario"
    destinatario_rol: Optional[str] = None  # "cliente"|"empleada"|"admin" si destinatario_tipo=="rol"


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


# ── ENDPOINTS ADMIN ─────────────────────────────────────────────────────────

@router.get("/admin/todas")
def get_all_notificaciones_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Obtiene todas las notificaciones del sistema (vista admin)"""
    try:
        repo = NotificacionRepository(db)
        notificaciones = repo.get_all_with_details(skip=skip, limit=limit)
        total = db.query(__import__('app.domain.models.notificacion', fromlist=['NotificacionServicio']).NotificacionServicio).count()

        result = []
        for n in notificaciones:
            d = n.to_dict()
            if n.usuario_destino:
                d["usuario_destino"] = {
                    "id": str(n.usuario_destino.id),
                    "nombre": n.usuario_destino.nombre,
                    "apellido": n.usuario_destino.apellido,
                    "correo": n.usuario_destino.correo,
                    "rol": n.usuario_destino.rol,
                }
            result.append(d)

        leidas = sum(1 for n in notificaciones if n.leida)
        no_leidas = sum(1 for n in notificaciones if not n.leida)

        return {
            "notificaciones": result,
            "estadisticas": {
                "total": total,
                "leidas": leidas,
                "no_leidas": no_leidas,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener notificaciones: {str(e)}"
        )


@router.post("/admin/enviar")
def enviar_notificacion_admin(
    request: EnviarNotificacionRequest,
    db: Session = Depends(get_db)
):
    """
    Envía una notificación manual a un usuario específico o a todos los usuarios de un rol.
    """
    try:
        from app.domain.models.usuario import Usuario
        repo = NotificacionRepository(db)

        if request.destinatario_tipo == "usuario":
            if not request.destinatario_id:
                raise HTTPException(status_code=400, detail="Debe proporcionar destinatario_id")
            uid = UUID(request.destinatario_id)
            usuario = db.query(Usuario).filter(Usuario.id == uid).first()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            repo.create(
                id_usuario_destino=uid,
                tipo=request.tipo,
                mensaje=request.mensaje,
                canal=request.canal,
            )
            enviadas = 1

        elif request.destinatario_tipo == "rol":
            if not request.destinatario_rol:
                raise HTTPException(status_code=400, detail="Debe proporcionar destinatario_rol")
            usuarios = db.query(Usuario).filter(
                Usuario.rol == request.destinatario_rol,
                Usuario.estado == "activo"
            ).all()
            if not usuarios:
                raise HTTPException(status_code=404, detail="No se encontraron usuarios con ese rol")
            for u in usuarios:
                repo.create(
                    id_usuario_destino=u.id,
                    tipo=request.tipo,
                    mensaje=request.mensaje,
                    canal=request.canal,
                )
            enviadas = len(usuarios)

        else:
            raise HTTPException(status_code=400, detail="destinatario_tipo debe ser 'usuario' o 'rol'")

        return {
            "success": True,
            "message": f"Notificación enviada a {enviadas} usuario(s) exitosamente",
            "enviadas": enviadas,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar notificación: {str(e)}"
        )
