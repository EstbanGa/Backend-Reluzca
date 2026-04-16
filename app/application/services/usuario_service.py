from typing import List, Optional, Dict
from fastapi import HTTPException, status
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuariosEstadisticas, UsuariosRolResponse, UsuarioCompleteResponse
from app.domain.models.usuario import Usuario
import logging

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def get_estadisticas_usuarios(self) -> UsuariosEstadisticas:
        """Calcula y retorna estadísticas de usuarios"""
        all_usuarios = self.usuario_repository.get_all(skip=0, limit=10000)
        
        total = len(all_usuarios)
        admins = sum(1 for u in all_usuarios if u.rol == "admin")
        clientes = sum(1 for u in all_usuarios if u.rol == "cliente")
        empleadas = sum(1 for u in all_usuarios if u.rol == "empleada")
        activos = sum(1 for u in all_usuarios if u.estado == "activo")
        inactivos = sum(1 for u in all_usuarios if u.estado == "inactivo")
        pendientes = sum(1 for u in all_usuarios if u.estado == "pendiente")
        
        return UsuariosEstadisticas(
            total=total,
            admins=admins,
            clientes=clientes,
            empleadas=empleadas,
            activos=activos,
            inactivos=inactivos,
            pendientes=pendientes
        )

    def get_usuario(self, usuario_id: str) -> UsuarioResponse:
        """Obtiene un usuario por ID"""
        usuario = self.usuario_repository.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return UsuarioResponse.model_validate(usuario)

    def get_usuarios(self, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        """Obtiene todos los usuarios"""
        usuarios = self.usuario_repository.get_all(skip=skip, limit=limit)
        return [UsuarioResponse.model_validate(u) for u in usuarios]

    def get_usuarios_by_rol_con_stats(self, rol: str, skip: int = 0, limit: int = 100) -> UsuariosRolResponse:
        """Obtiene usuarios por rol con estadísticas"""
        usuarios = self.usuario_repository.get_by_rol(rol, skip=skip, limit=limit)
        usuarios_response = [UsuarioResponse.model_validate(u) for u in usuarios]
        estadisticas = self.get_estadisticas_usuarios()
        
        return UsuariosRolResponse(
            usuarios=usuarios_response,
            estadisticas=estadisticas
        )

    def get_usuarios_by_rol(self, rol: str, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        """Obtiene usuarios por rol"""
        usuarios = self.usuario_repository.get_by_rol(rol, skip=skip, limit=limit)
        return [UsuarioResponse.model_validate(u) for u in usuarios]
    
    def get_empleadas(self) -> List[dict]:
        """
        Obtiene la lista de todas las empleadas activas
        
        Retorna una lista simplificada con información básica de las empleadas
        """
        empleadas = self.usuario_repository.db.query(Usuario).filter(
            Usuario.rol == "empleada",
            Usuario.estado == "activo"
        ).all()
        
        result = []
        for empleada in empleadas:
            result.append({
                "id": str(empleada.id),
                "nombre": empleada.nombre,
                "apellido": empleada.apellido,
                "nombre_completo": f"{empleada.nombre} {empleada.apellido}",
                "telefono": empleada.telefono,
                # TODO: Agregar ranking cuando se implemente sistema de calificaciones
                "ranking": 0
            })
        
        return result

    def search_usuarios(self, query: str, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        """Busca usuarios por nombre, apellido o email"""
        usuarios = self.usuario_repository.search(query, skip=skip, limit=limit)
        return [UsuarioResponse.model_validate(u) for u in usuarios]

    def create_usuario(self, usuario_data: UsuarioCreate) -> UsuarioResponse:
        """Crea el perfil del usuario en la BD (Supabase Auth gestiona la contraseña)"""
        logger.info(f"Creando usuario: {usuario_data.correo}, rol: {usuario_data.rol}")
        
        existing_user = self.usuario_repository.get_by_email(usuario_data.correo)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        valid_roles = ["cliente", "empleada", "admin"]
        if usuario_data.rol not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}"
            )

        if usuario_data.rol == "empleada":
            usuario_data.estado = "activo"
        
        usuario = self.usuario_repository.create(usuario_data)
        logger.info(f"Usuario creado: {usuario.correo}")
        return UsuarioResponse.model_validate(usuario)

    def update_usuario(self, usuario_id: str, usuario_data: UsuarioUpdate) -> UsuarioResponse:
        """Actualiza un usuario existente"""
        # Verificar que el usuario existe
        existing_user = self.usuario_repository.get_by_id(usuario_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Si se actualiza el email, verificar que no esté en uso
        if usuario_data.correo and usuario_data.correo != existing_user.correo:
            email_in_use = self.usuario_repository.get_by_email(usuario_data.correo)
            if email_in_use:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado"
                )

        # Si se actualiza el rol, validar
        if usuario_data.rol:
            valid_roles = ["cliente", "empleada", "admin"]
            if usuario_data.rol not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}"
                )

        # Hash de la contraseña si se proporciona
        # Actualizar usuario
        usuario = self.usuario_repository.update(usuario_id, usuario_data)
        return UsuarioResponse.model_validate(usuario)

    def delete_usuario(self, usuario_id: str) -> dict:
        """Elimina un usuario"""
        success = self.usuario_repository.delete(usuario_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return {"message": "Usuario eliminado exitosamente"}

    def deactivate_usuario(self, usuario_id: str) -> UsuarioResponse:
        """Desactiva un usuario"""
        usuario = self.usuario_repository.deactivate(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return UsuarioResponse.model_validate(usuario)

    def get_usuario_complete_info(self, usuario_id: str) -> UsuarioCompleteResponse:
        """
        Obtiene TODA la información del usuario incluyendo:
        - Datos del perfil
        - Reservas como cliente
        - Reservas como empleada
        - Ubicaciones de servicio
        - Ubicaciones de empleada
        """
        usuario = self.usuario_repository.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Convertir a dict para agregar relaciones
        usuario_dict = {
            "id": usuario.id,
            "rol": usuario.rol,
            "fecha_registro": usuario.fecha_registro,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.correo,  # Mapear correo a email
            "documento": usuario.documento,
            "telefono": usuario.telefono,
            "tipo_persona": usuario.tipo_persona,
            "fecha_nacimiento": usuario.fecha_nacimiento,
            "estado": usuario.estado,
            "ranking": usuario.ranking,
            "created_at": usuario.created_at,
            "updated_at": usuario.updated_at,
            "reservas_cliente": [],
            "reservas_empleada": [],
            "ubicaciones": [],
            "ubicaciones_empleada": []
        }
        
        # Cargar reservas como cliente
        if hasattr(usuario, 'reservas_cliente') and usuario.reservas_cliente:
            usuario_dict["reservas_cliente"] = [
                {
                    "id": r.id,
                    "fecha": r.fecha,
                    "hora_inicio": r.hora_inicio,
                    "hora_final": r.hora_final,
                    "estado": r.estado,
                    "estado_pago": r.estado_pago,
                    "precio_total": float(r.precio_total) if r.precio_total else None,
                    "descripcion": r.descripcion,
                    "plan": {
                        "id": r.plan.id if r.plan else None,
                        "nombre": r.plan.nombre if r.plan else None,
                        "precio": float(r.plan.precio) if r.plan and r.plan.precio else None
                    } if r.plan else None,
                    "empleada": {
                        "id": r.empleada.id if r.empleada else None,
                        "nombre": r.empleada.nombre if r.empleada else None,
                        "apellido": r.empleada.apellido if r.empleada else None,
                        "ranking": float(r.empleada.ranking) if r.empleada and r.empleada.ranking else None
                    } if r.empleada else None,
                    "lugar": {
                        "id": r.lugar.id if r.lugar else None,
                        "direccion": r.lugar.direccion if r.lugar else None
                    } if r.lugar else None
                }
                for r in usuario.reservas_cliente
            ]
        
        # Cargar reservas como empleada
        if hasattr(usuario, 'reservas_empleada') and usuario.reservas_empleada:
            usuario_dict["reservas_empleada"] = [
                {
                    "id": r.id,
                    "fecha": r.fecha,
                    "hora_inicio": r.hora_inicio,
                    "hora_final": r.hora_final,
                    "estado": r.estado,
                    "estado_pago": r.estado_pago,
                    "precio_total": float(r.precio_total) if r.precio_total else None,
                    "descripcion": r.descripcion,
                    "cliente": {
                        "id": r.cliente.id if r.cliente else None,
                        "nombre": r.cliente.nombre if r.cliente else None,
                        "apellido": r.cliente.apellido if r.cliente else None,
                        "telefono": r.cliente.telefono if r.cliente else None
                    } if r.cliente else None,
                    "plan": {
                        "id": r.plan.id if r.plan else None,
                        "nombre": r.plan.nombre if r.plan else None
                    } if r.plan else None
                }
                for r in usuario.reservas_empleada
            ]
        
        # Cargar ubicaciones de servicio (como cliente)
        if hasattr(usuario, 'ubicaciones') and usuario.ubicaciones:
            usuario_dict["ubicaciones"] = [
                {
                    "id": u.id,
                    "direccion": u.direccion,
                    "tamaño": u.tamaño,
                    "ubicacion": u.ubicacion,
                    "coordenadas": u.coordenadas,
                    "estado": u.estado,
                    "ciudad": u.ciudad,
                    "departamento": u.departamento
                }
                for u in usuario.ubicaciones
            ]
        
        # Cargar ubicaciones de empleada
        if hasattr(usuario, 'ubicaciones_empleada') and usuario.ubicaciones_empleada:
            usuario_dict["ubicaciones_empleada"] = [
                {
                    "id": u.id,
                    "direccion": u.direccion,
                    "ciudad": u.ciudad,
                    "departamento": u.departamento,
                    "coordenadas": u.coordenadas
                }
                for u in usuario.ubicaciones_empleada
            ]
        
        return UsuarioCompleteResponse(**usuario_dict)
