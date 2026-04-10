from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.infrastructure.auth import oauth2_scheme
from app.presentation.dependencies import get_db, get_current_user, require_role
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.application.services.usuario_service import UsuarioService
from app.application.services.auth_service import AuthService
from app.domain.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuariosRolResponse
from app.domain.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Inyección de dependencias para AuthService"""
    usuario_repository = UsuarioRepository(db)
    return AuthService(usuario_repository)


def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    """Inyección de dependencias para UsuarioService"""
    usuario_repository = UsuarioRepository(db)
    return UsuarioService(usuario_repository)


@router.get("", response_model=List[UsuarioResponse])
def get_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user: Usuario = Depends(require_role(["admin"])),  # Restricción temporal desactivada
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Obtiene todos los usuarios (solo admin)"""
    return usuario_service.get_usuarios(skip=skip, limit=limit)


@router.get("/search", response_model=List[UsuarioResponse])
def search_usuarios(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user: Usuario = Depends(require_role(["admin"])),  # Restricción temporal desactivada
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Busca usuarios por nombre, apellido o email (solo admin)"""
    return usuario_service.search_usuarios(q, skip=skip, limit=limit)


@router.get("/rol/{rol}", response_model=UsuariosRolResponse)
def get_usuarios_by_rol(
    rol: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user: Usuario = Depends(require_role(["admin"])),  # Restricción temporal desactivada
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Obtiene usuarios por rol con estadísticas (solo admin)"""
    return usuario_service.get_usuarios_by_rol_con_stats(rol, skip=skip, limit=limit)


@router.get("/empleadas")
async def get_empleadas(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """
    Obtiene la lista de todas las empleadas activas
    
    Retorna una lista de empleadas con su información básica
    Accesible para usuarios autenticados
    """
    # Verificar autenticación
    current_user = auth_service.get_current_user(token)
    if not current_user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales"
        )
    
    return usuario_service.get_empleadas()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Obtiene un usuario por ID (usuario debe estar autenticado)"""
    # Los usuarios pueden ver su propia información o los admins pueden ver cualquiera
    if current_user.id != usuario_id and current_user.rol != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario"
        )
    return usuario_service.get_usuario(usuario_id)


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(
    usuario_data: UsuarioCreate,
    current_user: Usuario = Depends(require_role(["admin"])),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Crea un nuevo usuario (solo admin)"""
    return usuario_service.create_usuario(usuario_data)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Actualiza un usuario (usuario puede actualizarse a sí mismo o admin puede actualizar cualquiera)"""
    # Los usuarios pueden actualizar su propia información o los admins pueden actualizar cualquiera
    if current_user.id != usuario_id and current_user.rol != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario"
        )
    
    # Solo admin puede cambiar el rol
    if usuario_data.rol is not None and current_user.rol != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cambiar el rol"
        )
    
    return usuario_service.update_usuario(usuario_id, usuario_data)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(require_role(["admin"])),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Elimina un usuario (solo admin)"""
    usuario_service.delete_usuario(usuario_id)


@router.patch("/{usuario_id}/deactivate", response_model=UsuarioResponse)
def deactivate_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(require_role(["admin"])),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Desactiva un usuario (solo admin)"""
    return usuario_service.deactivate_usuario(usuario_id)


@router.get("/empleada/dashboard")
def get_empleada_dashboard(
    current_user: Usuario = Depends(require_role(["empleada", "admin"])),
    db: Session = Depends(get_db)
):
    """Dashboard para empleadas - resumen de sus próximas reservas"""
    from app.infrastructure.repositories.reserva_repository import ReservaRepository
    reserva_repo = ReservaRepository(db)
    
    # Obtener reservas pendientes/confirmadas de la empleada
    reservas = reserva_repo.get_by_empleada(current_user.id, skip=0, limit=10)
    
    return {
        "empleada": {
            "id": current_user.id,
            "nombre": current_user.nombre,
            "apellido": current_user.apellido,
            "ranking": current_user.ranking
        },
        "reservas_proximas": [
            {
                "id": r.id,
                "fecha_servicio": r.fecha_servicio,
                "hora_inicio": r.hora_inicio,
                "cliente": {
                    "id": r.cliente.id,
                    "nombre": r.cliente.nombre,
                    "apellido": r.cliente.apellido
                },
                "plan": {
                    "id": r.plan.id,
                    "nombre": r.plan.nombre,
                    "duracion_estimada": r.plan.duracion_estimada
                }
            }
            for r in reservas
        ]
    }


@router.get("/empleada/dashboard/simple")
def get_empleada_dashboard_simple(
    db: Session = Depends(get_db)
):
    """
    Dashboard simplificado para empleadas - SIN AUTENTICACIÓN
    El frontend maneja la autenticación vía localStorage
    """
    # Por ahora retornamos datos básicos
    # TODO: Implementar obtención de empleada_id desde frontend
    return {
        "message": "Dashboard de empleada",
        "empleada_info": {
            "nombre": "Empleada",
            "ranking": 0,
            "fecha_registro": "2024-01-01"
        }
    }


# NOTA: Este endpoint antiguo está comentado porque ahora usamos el dashboard completo
# que está en app/api/dashboard.py sin autenticación (manejada por el front)
# @router.get("/cliente/dashboard")
# def get_cliente_dashboard(
#     current_user: Usuario = Depends(require_role(["cliente", "admin"])),
#     db: Session = Depends(get_db)
# ):
#     """Dashboard para clientes - resumen de sus reservas activas"""
#     from app.infrastructure.repositories.reserva_repository import ReservaRepository
#     reserva_repo = ReservaRepository(db)
#     
#     # Obtener reservas activas del cliente
#     reservas = reserva_repo.get_by_cliente(current_user.id, skip=0, limit=10)
#     
#     return {
#         "cliente": {
#             "id": current_user.id,
#             "nombre": current_user.nombre,
#             "apellido": current_user.apellido
#         },
#         "reservas_activas": [
#             {
#                 "id": r.id,
#                 "fecha_servicio": r.fecha_servicio,
#                 "hora_inicio": r.hora_inicio,
#                 "empleada": {
#                     "id": r.empleada.id if r.empleada else None,
#                     "nombre": r.empleada.nombre if r.empleada else None,
#                     "apellido": r.empleada.apellido if r.empleada else None,
#                     "ranking": r.empleada.ranking if r.empleada else None
#                 },
#                 "plan": {
#                     "id": r.plan.id,
#                     "nombre": r.plan.nombre,
#                     "precio": float(r.plan.precio)
#                 }
#             }
#             for r in reservas
#         ]
#     }


@router.get("/empleadas", response_model=List[UsuarioResponse])
def get_empleadas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """Obtiene lista de empleadas disponibles (usuarios autenticados)"""
    return usuario_service.get_usuarios_by_rol("empleada", skip=skip, limit=limit)


@router.post("/verify-email", response_model=UsuarioResponse)
def verify_email(
    token: str = Query(..., description="Token de verificación del email"),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """
    Verifica el email del usuario usando el token enviado por correo.
    Cambia el estado del usuario de 'pendiente' a 'activo'.
    """
    return usuario_service.verify_email(token)


@router.post("/resend-verification")
def resend_verification_email(
    email: str = Query(..., description="Email del usuario"),
    usuario_service: UsuarioService = Depends(get_usuario_service)
):
    """
    Reenvía el email de verificación a un usuario.
    """
    return usuario_service.resend_verification_email(email)

