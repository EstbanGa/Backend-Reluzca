from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException, status
from uuid import UUID
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.ubicacion_repository import UbicacionRepository
from app.schemas.reserva import ReservaCreate, ReservaUpdate, ReservaResponse


class ReservaService:
    def __init__(
        self,
        reserva_repository: ReservaRepository,
        usuario_repository: UsuarioRepository,
        plan_repository: PlanRepository,
        ubicacion_repository: UbicacionRepository
    ):
        self.reserva_repository = reserva_repository
        self.usuario_repository = usuario_repository
        self.plan_repository = plan_repository
        self.ubicacion_repository = ubicacion_repository

    def get_reserva(self, reserva_id: int) -> ReservaResponse:
        """Obtiene una reserva por ID"""
        reserva = self.reserva_repository.get_by_id(reserva_id)
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        return ReservaResponse.model_validate(reserva)

    def get_reservas(self, skip: int = 0, limit: int = 100) -> List[ReservaResponse]:
        """Obtiene todas las reservas"""
        reservas = self.reserva_repository.get_all(skip=skip, limit=limit)
        return [ReservaResponse.model_validate(r) for r in reservas]
    
    def get_reservas_with_stats(self, skip: int = 0, limit: int = 100) -> Dict:
        """
        Obtiene todas las reservas con estadísticas
        
        Retorna un dict con:
        - message: Mensaje de éxito
        - reservas: Lista de reservas con todos los detalles
        - estadisticas: Estadísticas de reservas
        """
        from sqlalchemy import func
        from app.models.reserva import Reserva
        
        # Obtener todas las reservas con relaciones cargadas
        reservas = self.reserva_repository.db.query(Reserva).order_by(
            Reserva.fecha.desc(),
            Reserva.hora_inicio.desc()
        ).all()
        
        # Calcular estadísticas
        total = len(reservas)
        activas = len([r for r in reservas if r.estado in ["confirmada", "en_proceso", "programada"]])
        completadas = len([r for r in reservas if r.estado == "completada"])
        canceladas = len([r for r in reservas if r.estado == "cancelada"])
        pendientes = len([r for r in reservas if r.estado == "pendiente"])
        
        # Convertir reservas a dict con todos los detalles
        reservas_list = []
        for reserva in reservas:
            reserva_dict = {
                "id": str(reserva.id),
                "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
                "hora_inicio": reserva.hora_inicio.strftime('%H:%M:%S') if reserva.hora_inicio else None,
                "hora_final": reserva.hora_final.strftime('%H:%M:%S') if reserva.hora_final else None,
                "estado": reserva.estado,
                "descripcion": reserva.descripcion,
                "precio_total": float(reserva.precio_total) if reserva.precio_total else 0,
                "created_at": reserva.created_at.isoformat() if reserva.created_at else None,
                "updated_at": reserva.updated_at.isoformat() if reserva.updated_at else None,
            }
            
            # Agregar información del cliente
            if reserva.cliente:
                reserva_dict["cliente"] = {
                    "id": str(reserva.cliente.id),
                    "nombre": reserva.cliente.nombre,
                    "apellido": reserva.cliente.apellido,
                    "correo": reserva.cliente.correo,
                    "telefono": reserva.cliente.telefono,
                    "fecha_registro": reserva.cliente.created_at.isoformat() if reserva.cliente.created_at else None
                }
            else:
                reserva_dict["cliente"] = None
            
            # Agregar información de empleada si existe
            if reserva.empleada:
                reserva_dict["empleada"] = {
                    "id": str(reserva.empleada.id),
                    "nombre": reserva.empleada.nombre,
                    "apellido": reserva.empleada.apellido,
                    "telefono": reserva.empleada.telefono,
                    "ranking": float(reserva.empleada.ranking) if reserva.empleada.ranking else None
                }
            else:
                reserva_dict["empleada"] = None
            
            # Agregar información del plan si existe
            if reserva.plan:
                reserva_dict["plan"] = {
                    "id": str(reserva.plan.id),
                    "nombre": reserva.plan.nombre,
                    "precio": float(reserva.plan.precio) if reserva.plan.precio else 0,
                    "duracion": reserva.plan.duracion if hasattr(reserva.plan, "duracion") else None,
                    "descripcion": reserva.plan.descripcion if hasattr(reserva.plan, "descripcion") else None
                }
            else:
                reserva_dict["plan"] = None
            
            # Agregar información del lugar si existe
            if reserva.lugar:
                lugar_dict = {
                    "id": str(reserva.lugar.id),
                    "nombre": reserva.lugar.nombre if hasattr(reserva.lugar, "nombre") else None,
                    "direccion": reserva.lugar.direccion if hasattr(reserva.lugar, "direccion") else None,
                    "tipo_lugar": reserva.lugar.tipo_lugar if hasattr(reserva.lugar, "tipo_lugar") else None,
                }
                
                # Agregar ubicación si existe
                if hasattr(reserva.lugar, "lat") and hasattr(reserva.lugar, "lng"):
                    lugar_dict["ubicacion"] = {
                        "lat": float(reserva.lugar.lat) if reserva.lugar.lat else None,
                        "lng": float(reserva.lugar.lng) if reserva.lugar.lng else None,
                        "formatted_address": reserva.lugar.formatted_address if hasattr(reserva.lugar, "formatted_address") else None
                    }
                
                reserva_dict["lugar"] = lugar_dict
            else:
                reserva_dict["lugar"] = None
            
            reservas_list.append(reserva_dict)
        
        # Calcular información de paginación
        import math
        items_per_page = limit if limit > 0 else 100
        current_page = (skip // items_per_page) + 1 if items_per_page > 0 else 1
        total_pages = math.ceil(total / items_per_page) if items_per_page > 0 else 1
        
        return {
            "message": "Reservas obtenidas exitosamente",
            "reservas": reservas_list,
            "estadisticas": {
                "total": total,
                "total_filtradas": total,
                "activas": activas,
                "completadas": completadas,
                "canceladas": canceladas,
                "pendientes": pendientes
            },
            "paginacion": {
                "current_page": current_page,
                "total_pages": total_pages,
                "total_items": total,
                "items_per_page": items_per_page,
                "has_next": current_page < total_pages,
                "has_previous": current_page > 1,
                "next_page": current_page + 1 if current_page < total_pages else None,
                "previous_page": current_page - 1 if current_page > 1 else None
            }
        }

    def get_reservas_by_cliente(self, cliente_id: int, skip: int = 0, limit: int = 100) -> List[ReservaResponse]:
        """Obtiene reservas por cliente"""
        reservas = self.reserva_repository.get_by_cliente(cliente_id, skip=skip, limit=limit)
        return [ReservaResponse.model_validate(r) for r in reservas]
    
    def get_reservas_by_cliente_with_stats(self, cliente_id: UUID) -> Dict:
        """
        Obtiene reservas por cliente con estadísticas
        
        Retorna un dict con:
        - message: Mensaje de éxito
        - reservas: Lista de reservas con todos los detalles
        - estadisticas: Estadísticas de reservas
        """
        from sqlalchemy import func
        from app.models.reserva import Reserva
        
        # Obtener todas las reservas del cliente con relaciones cargadas
        reservas = self.reserva_repository.db.query(Reserva).filter(
            Reserva.id_usuario == cliente_id
        ).order_by(
            Reserva.fecha.desc(),
            Reserva.hora_inicio.desc()
        ).all()
        
        # Calcular estadísticas
        total = len(reservas)
        activas = len([r for r in reservas if r.estado in ["confirmada", "en_proceso", "programada"]])
        completadas = len([r for r in reservas if r.estado == "completada"])
        canceladas = len([r for r in reservas if r.estado == "cancelada"])
        pendientes = len([r for r in reservas if r.estado == "pendiente"])
        
        # Convertir reservas a dict con todos los detalles
        reservas_list = []
        for reserva in reservas:
            reserva_dict = {
                "id": str(reserva.id),
                "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
                "hora_inicio": reserva.hora_inicio.strftime('%H:%M:%S') if reserva.hora_inicio else None,
                "hora_final": reserva.hora_final.strftime('%H:%M:%S') if reserva.hora_final else None,
                "estado": reserva.estado,
                "descripcion": reserva.descripcion,
                "precio_total": float(reserva.precio_total) if reserva.precio_total else 0,
                "created_at": reserva.created_at.isoformat() if reserva.created_at else None,
                "updated_at": reserva.updated_at.isoformat() if reserva.updated_at else None,
            }
            
            # Agregar información de empleada si existe
            if reserva.empleada:
                reserva_dict["empleada"] = {
                    "id": str(reserva.empleada.id),
                    "nombre": reserva.empleada.nombre,
                    "apellido": reserva.empleada.apellido,
                    "telefono": reserva.empleada.telefono,
                    "ranking": float(reserva.empleada.ranking) if reserva.empleada.ranking else None
                }
            else:
                reserva_dict["empleada"] = None
            
            # Agregar información del plan si existe
            if reserva.plan:
                reserva_dict["plan"] = {
                    "id": str(reserva.plan.id),
                    "nombre": reserva.plan.nombre,
                    "precio": float(reserva.plan.precio) if reserva.plan.precio else 0,
                    "duracion": reserva.plan.duracion if hasattr(reserva.plan, "duracion") else None
                }
            else:
                reserva_dict["plan"] = None
            
            # Agregar información del lugar si existe
            if reserva.lugar:
                reserva_dict["lugar"] = {
                    "id": str(reserva.lugar.id),
                    "nombre": reserva.lugar.nombre,
                    "direccion": reserva.lugar.ubicacion.get("direccion", "") if reserva.lugar.ubicacion else "",
                    "tipo_lugar": reserva.lugar.tipo_lugar
                }
            else:
                reserva_dict["lugar"] = None
            
            reservas_list.append(reserva_dict)
        
        return {
            "message": "Reservas obtenidas exitosamente",
            "reservas": reservas_list,
            "estadisticas": {
                "total": total,
                "activas": activas,
                "completadas": completadas,
                "canceladas": canceladas,
                "pendientes": pendientes
            }
        }

    def get_reservas_by_empleada(self, empleada_id: int, skip: int = 0, limit: int = 100) -> List[ReservaResponse]:
        """Obtiene reservas por empleada"""
        reservas = self.reserva_repository.get_by_empleada(empleada_id, skip=skip, limit=limit)
        return [ReservaResponse.model_validate(r) for r in reservas]

    def get_reservas_by_ubicacion(self, ubicacion_id: int, skip: int = 0, limit: int = 100) -> List[ReservaResponse]:
        """Obtiene reservas por ubicación"""
        reservas = self.reserva_repository.get_by_ubicacion(ubicacion_id, skip=skip, limit=limit)
        return [ReservaResponse.model_validate(r) for r in reservas]

    def get_reservas_by_estado(self, estado: str, skip: int = 0, limit: int = 100) -> List[ReservaResponse]:
        """Obtiene reservas por estado"""
        reservas = self.reserva_repository.get_by_estado(estado, skip=skip, limit=limit)
        return [ReservaResponse.model_validate(r) for r in reservas]

    def create_reserva(self, reserva_data: ReservaCreate) -> ReservaResponse:
        """Crea una nueva reserva"""
        # Validar que el cliente existe y tiene rol cliente
        cliente = self.usuario_repository.get_by_id(reserva_data.cliente_id)
        if not cliente or cliente.rol != "cliente":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente no existe o no tiene el rol correcto"
            )

        # Validar que la empleada existe y tiene rol empleada (si se proporciona)
        if reserva_data.empleada_id:
            empleada = self.usuario_repository.get_by_id(reserva_data.empleada_id)
            if not empleada or empleada.rol != "empleada":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La empleada no existe o no tiene el rol correcto"
                )

        # Validar que el plan existe y está activo
        plan = self.plan_repository.get_by_id(reserva_data.plan_id)
        if not plan or not plan.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El plan no existe o no está activo"
            )

        # Validar que la ubicación existe y está activa
        ubicacion = self.ubicacion_repository.get_by_id(reserva_data.ubicacion_id)
        if not ubicacion or not ubicacion.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La ubicación no existe o no está activa"
            )

        # Validar estado
        valid_estados = ["pendiente", "confirmada", "en_proceso", "completada", "cancelada"]
        if reserva_data.estado not in valid_estados:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_estados)}"
            )

        # Crear reserva
        reserva = self.reserva_repository.create(reserva_data)
        return ReservaResponse.model_validate(reserva)

    def update_reserva(self, reserva_id: int, reserva_data: ReservaUpdate) -> ReservaResponse:
        """Actualiza una reserva existente"""
        # Verificar que la reserva existe
        existing_reserva = self.reserva_repository.get_by_id(reserva_id)
        if not existing_reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Validar empleada si se actualiza
        if reserva_data.empleada_id:
            empleada = self.usuario_repository.get_by_id(reserva_data.empleada_id)
            if not empleada or empleada.rol != "empleada":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La empleada no existe o no tiene el rol correcto"
                )

        # Validar plan si se actualiza
        if reserva_data.plan_id:
            plan = self.plan_repository.get_by_id(reserva_data.plan_id)
            if not plan or not plan.activo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El plan no existe o no está activo"
                )

        # Validar ubicación si se actualiza
        if reserva_data.ubicacion_id:
            ubicacion = self.ubicacion_repository.get_by_id(reserva_data.ubicacion_id)
            if not ubicacion or not ubicacion.activo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La ubicación no existe o no está activa"
                )

        # Validar estado si se actualiza
        if reserva_data.estado:
            valid_estados = ["pendiente", "confirmada", "en_proceso", "completada", "cancelada"]
            if reserva_data.estado not in valid_estados:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_estados)}"
                )

        # Actualizar reserva
        reserva = self.reserva_repository.update(reserva_id, reserva_data)
        return ReservaResponse.model_validate(reserva)

    def delete_reserva(self, reserva_id: int) -> dict:
        """Elimina una reserva"""
        success = self.reserva_repository.delete(reserva_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        return {"message": "Reserva eliminada exitosamente"}

    def cancel_reserva(self, reserva_id: int) -> ReservaResponse:
        """Cancela una reserva"""
        reserva = self.reserva_repository.cancel(reserva_id)
        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )
        return ReservaResponse.model_validate(reserva)
