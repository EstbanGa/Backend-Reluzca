"""API endpoints para dashboard"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import ClienteDashboardResponse
from app.models.usuario import Usuario

router = APIRouter(prefix="/usuarios/cliente", tags=["Dashboard Cliente"])


@router.get("/dashboard", response_model=ClienteDashboardResponse)
def get_cliente_dashboard(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene toda la información del dashboard del cliente
    
    Parámetros:
    - usuario_id: ID del usuario cliente
    
    Retorna:
    - Información del cliente
    - Estadísticas de reservas
    - Estadísticas de ubicaciones
    - Datos principales (reservas recientes, próximas, empleadas frecuentes, etc.)
    - Información del sistema (notificaciones)
    """
    try:
        # Obtener dashboard directamente
        dashboard_service = DashboardService(db)
        dashboard_data = dashboard_service.get_cliente_dashboard(usuario_id)
        
        return dashboard_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dashboard: {str(e)}"
        )

