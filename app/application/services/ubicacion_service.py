from typing import List, Optional, Dict
from fastapi import HTTPException, status
from uuid import UUID
from app.infrastructure.repositories.ubicacion_repository import UbicacionRepository
from app.domain.schemas.ubicacion import UbicacionServicioCreate, UbicacionServicioUpdate, UbicacionServicioResponse


class UbicacionService:
    def __init__(self, ubicacion_repository: UbicacionRepository):
        self.ubicacion_repository = ubicacion_repository

    def get_ubicacion(self, ubicacion_id: int) -> UbicacionServicioResponse:
        """Obtiene una ubicación por ID"""
        ubicacion = self.ubicacion_repository.get_by_id(ubicacion_id)
        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )
        return UbicacionServicioResponse.model_validate(ubicacion)

    def get_ubicaciones(self, skip: int = 0, limit: int = 100, activo_only: bool = False) -> List[UbicacionServicioResponse]:
        """Obtiene todas las ubicaciones"""
        ubicaciones = self.ubicacion_repository.get_all(skip=skip, limit=limit, activo_only=activo_only)
        return [UbicacionServicioResponse.model_validate(u) for u in ubicaciones]

    def get_ubicaciones_by_usuario(self, usuario_id: str, skip: int = 0, limit: int = 100) -> List[UbicacionServicioResponse]:
        """Obtiene ubicaciones por usuario"""
        ubicaciones = self.ubicacion_repository.get_by_usuario(usuario_id, skip=skip, limit=limit)
        return [UbicacionServicioResponse.model_validate(u) for u in ubicaciones]
    
    def get_ubicaciones_by_usuario_with_stats(self, usuario_id: UUID) -> Dict:
        """
        Obtiene ubicaciones por usuario con estadísticas
        
        Retorna un dict con:
        - message: Mensaje de éxito
        - ubicaciones: Lista de ubicaciones con todos los detalles
        - estadisticas: Estadísticas de ubicaciones
        """
        from app.domain.models.ubicacion import UbicacionServicio
        
        # Obtener todas las ubicaciones del usuario con ordenamiento
        ubicaciones = self.ubicacion_repository.db.query(UbicacionServicio).filter(
            UbicacionServicio.id_usuario == usuario_id
        ).order_by(
            UbicacionServicio.created_at.desc()
        ).all()
        
        # Calcular estadísticas
        total = len(ubicaciones)
        activas = len([u for u in ubicaciones if u.estado])
        inactivas = len([u for u in ubicaciones if not u.estado])
        
        # Calcular estadísticas por tamaño
        estadisticas_tamanos = {}
        for ubicacion in ubicaciones:
            if ubicacion.tamaño and isinstance(ubicacion.tamaño, dict):
                categoria = ubicacion.tamaño.get('categoria')
                if categoria:
                    estadisticas_tamanos[categoria] = estadisticas_tamanos.get(categoria, 0) + 1
        
        # Convertir ubicaciones a dict con todos los detalles
        ubicaciones_list = []
        for ubicacion in ubicaciones:
            # Procesar tamaño
            tamaño_procesado = None
            if ubicacion.tamaño:
                if isinstance(ubicacion.tamaño, dict):
                    tamaño_procesado = {
                        "categoria": ubicacion.tamaño.get("categoria"),
                        "metros": ubicacion.tamaño.get("metros"),
                        "unidad": ubicacion.tamaño.get("unidad", "m²"),
                        "display": f"{ubicacion.tamaño.get('metros', 0)} {ubicacion.tamaño.get('unidad', 'm²')}" if ubicacion.tamaño.get('metros') else ubicacion.tamaño.get("categoria", "N/A")
                    }
            
            # Procesar ubicación/dirección
            ubicacion_procesada = None
            if ubicacion.ubicacion:
                if isinstance(ubicacion.ubicacion, dict):
                    ubicacion_procesada = {
                        "lat": ubicacion.ubicacion.get("lat"),
                        "lng": ubicacion.ubicacion.get("lng"),
                        "direccion": ubicacion.ubicacion.get("direccion"),
                        "formatted_address": ubicacion.ubicacion.get("formatted_address") or ubicacion.ubicacion.get("direccion")
                    }
            
            ubicacion_dict = {
                "id": str(ubicacion.id),
                "nombre": ubicacion.nombre,
                "tamaño": tamaño_procesado,
                "baños": ubicacion.baños,
                "pisos": ubicacion.pisos,
                "ubicacion": ubicacion_procesada,
                "nombre_lugar": ubicacion.nombre_lugar,
                "tipo_lugar": ubicacion.tipo_lugar,
                "estado": ubicacion.estado,
                "descripcion": ubicacion.descripcion,
                "created_at": ubicacion.created_at.isoformat() if ubicacion.created_at else None,
                "updated_at": ubicacion.updated_at.isoformat() if ubicacion.updated_at else None,
            }
            
            ubicaciones_list.append(ubicacion_dict)
        
        return {
            "message": "Ubicaciones obtenidas exitosamente",
            "ubicaciones": ubicaciones_list,
            "estadisticas": {
                "total": total,
                "activas": activas,
                "inactivas": inactivas,
                "por_tamano": estadisticas_tamanos
            }
        }

    def search_ubicaciones(self, query: str, skip: int = 0, limit: int = 100) -> List[UbicacionServicioResponse]:
        """Busca ubicaciones por nombre o tipo"""
        ubicaciones = self.ubicacion_repository.search(query, skip=skip, limit=limit)
        return [UbicacionServicioResponse.model_validate(u) for u in ubicaciones]

    def create_ubicacion(self, ubicacion_data: UbicacionServicioCreate) -> UbicacionServicioResponse:
        """Crea una nueva ubicación"""
        # Crear ubicación
        ubicacion = self.ubicacion_repository.create(ubicacion_data)
        return UbicacionServicioResponse.model_validate(ubicacion)

    def update_ubicacion(self, ubicacion_id: int, ubicacion_data: UbicacionServicioUpdate) -> UbicacionServicioResponse:
        """Actualiza una ubicación existente"""
        # Verificar que la ubicación existe
        existing_ubicacion = self.ubicacion_repository.get_by_id(ubicacion_id)
        if not existing_ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )

        # Actualizar ubicación
        ubicacion = self.ubicacion_repository.update(ubicacion_id, ubicacion_data)
        return UbicacionServicioResponse.model_validate(ubicacion)

    def delete_ubicacion(self, ubicacion_id: int) -> dict:
        """Elimina una ubicación"""
        success = self.ubicacion_repository.delete(ubicacion_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )
        return {"message": "Ubicación eliminada exitosamente"}

    def deactivate_ubicacion(self, ubicacion_id: int) -> UbicacionServicioResponse:
        """Desactiva una ubicación"""
        ubicacion = self.ubicacion_repository.deactivate(ubicacion_id)
        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )
        return UbicacionServicioResponse.model_validate(ubicacion)
