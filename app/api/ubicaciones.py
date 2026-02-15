from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.auth import oauth2_scheme
from app.core.dependencies import get_db, get_current_user, require_role
from app.repositories.ubicacion_repository import UbicacionRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.ubicacion_service import UbicacionService
from app.services.auth_service import AuthService
from app.schemas.ubicacion import UbicacionServicioCreate, UbicacionServicioUpdate, UbicacionServicioResponse
from app.models.usuario import Usuario

router = APIRouter(prefix="/ubicaciones", tags=["ubicaciones"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Inyección de dependencias para AuthService"""
    usuario_repository = UsuarioRepository(db)
    return AuthService(usuario_repository)


def get_ubicacion_service(db: Session = Depends(get_db)) -> UbicacionService:
    """Inyección de dependencias para UbicacionService"""
    ubicacion_repository = UbicacionRepository(db)
    return UbicacionService(ubicacion_repository)


@router.get("/", response_model=List[UbicacionServicioResponse])
def get_ubicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    activo_only: bool = Query(False),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Obtiene todas las ubicaciones (público)"""
    return ubicacion_service.get_ubicaciones(skip=skip, limit=limit, activo_only=activo_only)


@router.get("/search", response_model=List[UbicacionServicioResponse])
def search_ubicaciones(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Busca ubicaciones por nombre o tipo (público)"""
    return ubicacion_service.search_ubicaciones(q, skip=skip, limit=limit)


@router.get("/cliente/{usuario_id}")
def get_ubicaciones_by_cliente(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene ubicaciones de un cliente con estadísticas
    SIN AUTENTICACIÓN - El frontend maneja la autenticación
    
    Retorna:
    - message: Mensaje de éxito
    - ubicaciones: Lista de ubicaciones con todos los detalles
    - estadisticas: Estadísticas de ubicaciones (total, activas, inactivas, por_tamano)
    """
    try:
        # Instanciar servicios manualmente (sin dependencias de auth)
        ubicacion_repository = UbicacionRepository(db)
        ubicacion_service = UbicacionService(ubicacion_repository)
        
        # Obtener ubicaciones con estadísticas
        result = ubicacion_service.get_ubicaciones_by_usuario_with_stats(usuario_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ubicaciones: {str(e)}"
        )


@router.get("/{ubicacion_id}", response_model=UbicacionServicioResponse)
def get_ubicacion(
    ubicacion_id: int,
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Obtiene una ubicación por ID (público)"""
    return ubicacion_service.get_ubicacion(ubicacion_id)


@router.post("/cliente/crear")
def create_ubicacion_cliente(
    ubicacion_data: UbicacionServicioCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva ubicación para un cliente
    SIN AUTENTICACIÓN - El frontend maneja la autenticación via localStorage
    """
    try:
        ubicacion_repository = UbicacionRepository(db)
        ubicacion_service = UbicacionService(ubicacion_repository)
        
        ubicacion = ubicacion_service.create_ubicacion(ubicacion_data)
        
        return {
            "success": True,
            "message": "Ubicación creada exitosamente",
            "ubicacion": {
                "id": str(ubicacion.id),
                "nombre": ubicacion.nombre,
                "tipo_lugar": ubicacion.tipo_lugar,
                "estado": ubicacion.estado
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear ubicación: {str(e)}"
        )


@router.put("/cliente/{ubicacion_id}")
def update_ubicacion_cliente(
    ubicacion_id: str,
    ubicacion_data: UbicacionServicioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una ubicación para un cliente
    SIN AUTENTICACIÓN - El frontend maneja la autenticación via localStorage
    """
    try:
        ubicacion_repository = UbicacionRepository(db)
        ubicacion_service = UbicacionService(ubicacion_repository)
        
        ubicacion = ubicacion_service.update_ubicacion(ubicacion_id, ubicacion_data)
        
        return {
            "success": True,
            "message": "Ubicación actualizada exitosamente",
            "ubicacion": {
                "id": str(ubicacion.id),
                "nombre": ubicacion.nombre,
                "tipo_lugar": ubicacion.tipo_lugar,
                "estado": ubicacion.estado
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar ubicación: {str(e)}"
        )


@router.post("/", response_model=UbicacionServicioResponse, status_code=status.HTTP_201_CREATED)
def create_ubicacion(
    ubicacion_data: UbicacionServicioCreate,
    current_user: Usuario = Depends(require_role(["admin"])),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Crea una nueva ubicación (solo admin)"""
    return ubicacion_service.create_ubicacion(ubicacion_data)


@router.put("/{ubicacion_id}", response_model=UbicacionServicioResponse)
def update_ubicacion(
    ubicacion_id: int,
    ubicacion_data: UbicacionServicioUpdate,
    current_user: Usuario = Depends(require_role(["admin"])),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Actualiza una ubicación (solo admin)"""
    return ubicacion_service.update_ubicacion(ubicacion_id, ubicacion_data)


@router.delete("/{ubicacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ubicacion(
    ubicacion_id: int,
    current_user: Usuario = Depends(require_role(["admin"])),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Elimina una ubicación (solo admin)"""
    ubicacion_service.delete_ubicacion(ubicacion_id)


@router.patch("/{ubicacion_id}/deactivate", response_model=UbicacionServicioResponse)
def deactivate_ubicacion(
    ubicacion_id: int,
    current_user: Usuario = Depends(require_role(["admin"])),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    """Desactiva una ubicación (solo admin)"""
    return ubicacion_service.deactivate_ubicacion(ubicacion_id)
