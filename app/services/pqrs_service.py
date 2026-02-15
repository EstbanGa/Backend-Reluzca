"""
PQRS Service - Business logic for PQRS management.
"""
from app.repositories.pqrs_repository import PQRSRepository
from typing import Dict, Any, List
from datetime import datetime


class PQRSService:
    """Service for PQRS business logic."""
    
    def __init__(self, pqrs_repository: PQRSRepository):
        self.pqrs_repository = pqrs_repository
    
    def get_pqrs_by_usuario_with_stats(self, usuario_id: str) -> Dict[str, Any]:
        """Get all PQRS for a user with statistics."""
        pqrs_list = self.pqrs_repository.get_by_usuario(usuario_id)
        
        # Calculate statistics
        total = len(pqrs_list)
        pendientes = len([p for p in pqrs_list if p.estado == "pendiente"])
        en_proceso = len([p for p in pqrs_list if p.estado == "en_proceso"])
        resueltos = len([p for p in pqrs_list if p.estado == "resuelto"])
        cerrados = len([p for p in pqrs_list if p.estado == "cerrado"])
        
        # Count by type
        por_tipo = {}
        for pqrs in pqrs_list:
            tipo = pqrs.tipo
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        # Count by priority
        por_prioridad = {}
        for pqrs in pqrs_list:
            prioridad = pqrs.prioridad or "media"
            por_prioridad[prioridad] = por_prioridad.get(prioridad, 0) + 1
        
        # Format PQRS data
        pqrs_formatted = []
        for pqrs in pqrs_list:
            pqrs_data = {
                "id": str(pqrs.id),
                "tipo": pqrs.tipo,
                "descripcion": pqrs.descripcion,
                "estado": pqrs.estado,
                "prioridad": pqrs.prioridad,
                "respuesta": pqrs.respuesta,
                "fecha_creacion": pqrs.fecha_creacion.isoformat() if pqrs.fecha_creacion else None,
                "fecha_resolucion": pqrs.fecha_resolucion.isoformat() if pqrs.fecha_resolucion else None,
                "created_at": pqrs.created_at.isoformat() if pqrs.created_at else None,
            }
            
            # Add empleada info if exists
            if pqrs.empleada:
                pqrs_data["empleada"] = {
                    "id": str(pqrs.empleada.id),
                    "nombre": pqrs.empleada.nombre,
                    "apellido": pqrs.empleada.apellido,
                }
            else:
                pqrs_data["empleada"] = None
            
            # Add reserva info if exists
            if pqrs.reserva:
                pqrs_data["reserva"] = {
                    "id": str(pqrs.reserva.id),
                    "fecha": pqrs.reserva.fecha.isoformat() if pqrs.reserva.fecha else None,
                }
            else:
                pqrs_data["reserva"] = None
            
            pqrs_formatted.append(pqrs_data)
        
        return {
            "message": "PQRS obtenidos exitosamente",
            "pqrs": pqrs_formatted,
            "estadisticas": {
                "total": total,
                "pendientes": pendientes,
                "en_proceso": en_proceso,
                "resueltos": resueltos,
                "cerrados": cerrados,
                "por_tipo": por_tipo,
                "por_prioridad": por_prioridad,
            }
        }
    
    def get_all_pqrs_with_stats(self) -> Dict[str, Any]:
        """Get all PQRS with statistics (for admin)."""
        pqrs_list = self.pqrs_repository.get_all()
        
        # Calculate statistics
        total = len(pqrs_list)
        pendientes = len([p for p in pqrs_list if p.estado == "pendiente"])
        en_proceso = len([p for p in pqrs_list if p.estado == "en_proceso"])
        resueltos = len([p for p in pqrs_list if p.estado == "resuelto"])
        cerrados = len([p for p in pqrs_list if p.estado == "cerrado"])
        
        # Count by type
        por_tipo = {}
        for pqrs in pqrs_list:
            tipo = pqrs.tipo
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        # Count by priority
        por_prioridad = {}
        for pqrs in pqrs_list:
            prioridad = pqrs.prioridad or "media"
            por_prioridad[prioridad] = por_prioridad.get(prioridad, 0) + 1
        
        # Format PQRS data
        pqrs_formatted = []
        for pqrs in pqrs_list:
            pqrs_data = {
                "id": str(pqrs.id),
                "tipo": pqrs.tipo,
                "descripcion": pqrs.descripcion,
                "estado": pqrs.estado,
                "prioridad": pqrs.prioridad,
                "respuesta": pqrs.respuesta,
                "fecha_creacion": pqrs.fecha_creacion.isoformat() if pqrs.fecha_creacion else None,
                "fecha_resolucion": pqrs.fecha_resolucion.isoformat() if pqrs.fecha_resolucion else None,
                "created_at": pqrs.created_at.isoformat() if pqrs.created_at else None,
            }
            
            # Add usuario info
            if pqrs.usuario:
                pqrs_data["usuario"] = {
                    "id": str(pqrs.usuario.id),
                    "nombre": pqrs.usuario.nombre,
                    "apellido": pqrs.usuario.apellido,
                    "email": pqrs.usuario.email,
                }
            else:
                pqrs_data["usuario"] = None
            
            # Add empleada info if exists
            if pqrs.empleada:
                pqrs_data["empleada"] = {
                    "id": str(pqrs.empleada.id),
                    "nombre": pqrs.empleada.nombre,
                    "apellido": pqrs.empleada.apellido,
                }
            else:
                pqrs_data["empleada"] = None
            
            # Add reserva info if exists
            if pqrs.reserva:
                pqrs_data["reserva"] = {
                    "id": str(pqrs.reserva.id),
                    "fecha": pqrs.reserva.fecha.isoformat() if pqrs.reserva.fecha else None,
                }
            else:
                pqrs_data["reserva"] = None
            
            pqrs_formatted.append(pqrs_data)
        
        return {
            "message": "PQRS obtenidos exitosamente",
            "pqrs": pqrs_formatted,
            "estadisticas": {
                "total": total,
                "pendientes": pendientes,
                "en_proceso": en_proceso,
                "resueltos": resueltos,
                "cerrados": cerrados,
                "por_tipo": por_tipo,
                "por_prioridad": por_prioridad,
            }
        }
    
    def responder_pqrs(self, pqrs_id: str, respuesta_data: Dict[str, Any]) -> Dict[str, Any]:
        """Respond to a PQRS and update its status."""
        pqrs = self.pqrs_repository.get_by_id(pqrs_id)
        
        if not pqrs:
            raise ValueError("PQRS no encontrado")
        
        # Update PQRS
        update_data = {
            "respuesta": respuesta_data.get("respuesta"),
            "estado": respuesta_data.get("estado", "resuelto"),
            "id_empleada": respuesta_data.get("id_empleada"),
            "fecha_resolucion": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        updated_pqrs = self.pqrs_repository.update(pqrs_id, update_data)
        
        return {
            "message": "PQRS respondido exitosamente",
            "pqrs": updated_pqrs.to_dict()
        }
    
    def create_pqrs(self, pqrs_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new PQRS."""
        # Set default values
        pqrs_data.setdefault("estado", "pendiente")
        pqrs_data.setdefault("prioridad", "media")
        pqrs_data.setdefault("fecha_creacion", datetime.utcnow())
        pqrs_data.setdefault("created_at", datetime.utcnow())
        pqrs_data.setdefault("updated_at", datetime.utcnow())
        
        pqrs = self.pqrs_repository.create(pqrs_data)
        
        return {
            "message": "PQRS creado exitosamente",
            "pqrs": pqrs.to_dict()
        }
