from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta, time
from app.core.auth import oauth2_scheme
from app.core.dependencies import get_db, get_current_user, require_role
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.ubicacion_repository import UbicacionRepository
from app.services.reserva_service import ReservaService
from app.services.auth_service import AuthService
from app.schemas.reserva import ReservaCreate, ReservaUpdate, ReservaResponse, ReservasWithStatsResponse
from app.models.usuario import Usuario
from pydantic import BaseModel

router = APIRouter(prefix="/reservas", tags=["reservas"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Inyección de dependencias para AuthService"""
    usuario_repository = UsuarioRepository(db)
    return AuthService(usuario_repository)


def get_reserva_service(db: Session = Depends(get_db)) -> ReservaService:
    """Inyección de dependencias para ReservaService"""
    reserva_repository = ReservaRepository(db)
    usuario_repository = UsuarioRepository(db)
    plan_repository = PlanRepository(db)
    ubicacion_repository = UbicacionRepository(db)
    return ReservaService(
        reserva_repository,
        usuario_repository,
        plan_repository,
        ubicacion_repository
    )


@router.get("", response_model=ReservasWithStatsResponse)
def get_reservas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    # current_user: Usuario = Depends(require_role(["admin", "empleada"])),  # Temporal
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Obtiene todas las reservas con estadísticas (admin y empleada)"""
    return reserva_service.get_reservas_with_stats(skip=skip, limit=limit)


@router.get("/cliente/{cliente_id}")
def get_reservas_by_cliente(
    cliente_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene reservas por cliente con estadísticas (SIN AUTENTICACIÓN)
    
    El frontend maneja la autenticación, este endpoint solo retorna datos
    
    Retorna:
    - Lista de reservas con detalles completos (empleada, plan, lugar)
    - Estadísticas de reservas (total, activas, completadas, canceladas, pendientes)
    """
    try:
        reserva_service = ReservaService(
            ReservaRepository(db),
            UsuarioRepository(db),
            PlanRepository(db),
            UbicacionRepository(db)
        )
        result = reserva_service.get_reservas_by_cliente_with_stats(cliente_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener reservas: {str(e)}"
        )


@router.get("/empleada/{empleada_id}", response_model=List[ReservaResponse])
def get_reservas_by_empleada(
    empleada_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Obtiene reservas por empleada (la empleada puede ver sus propias reservas o admin puede ver cualquiera)"""
    if current_user.id != empleada_id and current_user.rol != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estas reservas"
        )
    return reserva_service.get_reservas_by_empleada(empleada_id, skip=skip, limit=limit)


@router.get("/ubicacion/{ubicacion_id}", response_model=List[ReservaResponse])
def get_reservas_by_ubicacion(
    ubicacion_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Usuario = Depends(require_role(["admin", "empleada"])),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Obtiene reservas por ubicación (admin y empleada)"""
    return reserva_service.get_reservas_by_ubicacion(ubicacion_id, skip=skip, limit=limit)


@router.get("/estado/{estado}", response_model=List[ReservaResponse])
def get_reservas_by_estado(
    estado: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: Usuario = Depends(require_role(["admin", "empleada"])),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Obtiene reservas por estado (admin y empleada)"""
    return reserva_service.get_reservas_by_estado(estado, skip=skip, limit=limit)


@router.get("/{reserva_id}", response_model=ReservaResponse)
def get_reserva(
    reserva_id: int,
    current_user: Usuario = Depends(get_current_user),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Obtiene una reserva por ID"""
    reserva = reserva_service.get_reserva(reserva_id)
    
    # Verificar permisos
    if (current_user.rol not in ["admin", "empleada"] and 
        current_user.id != reserva.cliente_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta reserva"
        )
    
    return reserva


@router.post("/", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
def create_reserva(
    reserva_data: ReservaCreate,
    current_user: Usuario = Depends(get_current_user),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Crea una nueva reserva (cualquier usuario autenticado)"""
    # Los clientes solo pueden crear reservas para sí mismos
    if current_user.rol == "cliente" and current_user.id != reserva_data.cliente_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes crear reservas para ti mismo"
        )
    
    return reserva_service.create_reserva(reserva_data)


@router.put("/{reserva_id}", response_model=ReservaResponse)
def update_reserva(
    reserva_id: int,
    reserva_data: ReservaUpdate,
    current_user: Usuario = Depends(require_role(["admin", "empleada"])),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Actualiza una reserva (admin y empleada)"""
    return reserva_service.update_reserva(reserva_id, reserva_data)


@router.delete("/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reserva(
    reserva_id: int,
    current_user: Usuario = Depends(require_role(["admin"])),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Elimina una reserva (solo admin)"""
    reserva_service.delete_reserva(reserva_id)


@router.patch("/{reserva_id}/cancel", response_model=ReservaResponse)
def cancel_reserva(
    reserva_id: int,
    current_user: Usuario = Depends(get_current_user),
    reserva_service: ReservaService = Depends(get_reserva_service)
):
    """Cancela una reserva (el cliente puede cancelar sus propias reservas o admin/empleada puede cancelar cualquiera)"""
    reserva = reserva_service.get_reserva(reserva_id)
    
    if (current_user.rol not in ["admin", "empleada"] and 
        current_user.id != reserva.cliente_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta reserva"
        )
    
    return reserva_service.cancel_reserva(reserva_id)


@router.get("/planes/")
def get_planes_for_reserva(db: Session = Depends(get_db)):
    """
    Obtiene todos los planes disponibles para crear una reserva (SIN AUTENTICACIÓN)
    
    El frontend maneja la autenticación mediante localStorage
    """
    try:
        plan_repository = PlanRepository(db)
        planes = plan_repository.get_all()
        
        return {
            "success": True,
            "planes": [
                {
                    "id": str(plan.id),
                    "nombre": plan.nombre,
                    "descripcion": plan.descripcion,
                    "precio": float(plan.precio) if plan.precio else 0,
                    "duracion_estimada_horas": plan.horas_servicio if hasattr(plan, 'horas_servicio') else 4,
                    "servicios_asociados": plan.servicios_asociados if hasattr(plan, 'servicios_asociados') and plan.servicios_asociados else []
                }
                for plan in planes
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar planes: {str(e)}"
        )


@router.get("/ubicaciones/")
def get_ubicaciones_for_reserva(db: Session = Depends(get_db)):
    """
    Obtiene todas las ubicaciones del cliente autenticado para crear una reserva (SIN AUTENTICACIÓN)
    
    El frontend debe pasar el cliente_id como query param
    """
    try:
        # Por ahora retornamos todas las ubicaciones activas
        # El frontend debería filtrar por cliente_id
        ubicacion_repository = UbicacionRepository(db)
        ubicaciones = ubicacion_repository.get_all()
        
        return {
            "success": True,
            "ubicaciones": [
                {
                    "id": str(ubicacion.id),
                    "nombre": ubicacion.nombre,
                    "nombre_lugar": ubicacion.nombre_lugar,
                    "tipo_lugar": ubicacion.tipo_lugar,
                    "descripcion": ubicacion.descripcion,
                    "estado": ubicacion.estado,
                    "pisos": ubicacion.pisos if hasattr(ubicacion, 'pisos') and ubicacion.pisos else 1,
                    "baños": ubicacion.baños if hasattr(ubicacion, 'baños') and ubicacion.baños else 1
                }
                for ubicacion in ubicaciones
                if ubicacion.estado == True  # Boolean, no string
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar ubicaciones: {str(e)}"
        )


# Schemas para nuevos endpoints
class DisponibilidadDia(BaseModel):
    fecha: str
    disponible: bool
    es_sabado: bool
    es_domingo: bool
    dia_semana: str
    es_hoy: bool
    es_pasado: bool
    sobrecargo_sabado: bool


class HorarioDisponible(BaseModel):
    hora_inicio: str
    hora_final: str
    horas_duracion: int
    sobrecargo_sabado: float
    descripcion: str


class FechaHorario(BaseModel):
    fecha: str
    hora_inicio: str
    hora_final: str
    sobrecargo_sabado: float


class CalculoPrecioRequest(BaseModel):
    plan_id: str
    ubicacion_id: str
    fechas_horarios: List[FechaHorario]
    tareas_extra: List[str]


class CrearReservasRequest(BaseModel):
    empleada_id: str
    plan_id: str
    ubicacion_id: str
    fechas_horarios: List[FechaHorario]
    tareas_extra: List[str]


@router.get("/empleadas/{empleada_id}/disponibilidad")
async def get_disponibilidad_empleada(
    empleada_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la disponibilidad de una empleada para los próximos 60 días
    Excluye domingos ya que no trabajan domingos
    """
    try:
        usuario_repo = UsuarioRepository(db)
        empleada = usuario_repo.get_by_id(empleada_id)
        
        if not empleada or empleada.rol != "empleada" or empleada.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleada no encontrada"
            )
        
        # Obtener fecha actual y rango de 60 días
        fecha_actual = date.today()
        fecha_limite = fecha_actual + timedelta(days=60)
        
        # Obtener reservas ocupadas de la empleada
        reserva_repo = ReservaRepository(db)
        reservas = reserva_repo.get_by_empleada(empleada_id)
        
        fechas_ocupadas = set()
        for reserva in reservas:
            if (reserva.fecha >= fecha_actual and 
                reserva.fecha <= fecha_limite and
                reserva.estado in ['programada', 'en_progreso', 'completada']):
                fechas_ocupadas.add(reserva.fecha)
        
        # Generar calendario de disponibilidad
        calendario = []
        fecha_iteracion = fecha_actual
        
        while fecha_iteracion <= fecha_limite:
            es_domingo = fecha_iteracion.weekday() == 6
            es_sabado = fecha_iteracion.weekday() == 5
            
            disponible = (
                fecha_iteracion not in fechas_ocupadas and
                not es_domingo and
                fecha_iteracion >= fecha_actual
            )
            
            calendario.append({
                'fecha': fecha_iteracion.isoformat(),
                'disponible': disponible,
                'es_sabado': es_sabado,
                'es_domingo': es_domingo,
                'dia_semana': fecha_iteracion.strftime('%A'),
                'es_hoy': fecha_iteracion == fecha_actual,
                'es_pasado': fecha_iteracion < fecha_actual,
                'sobrecargo_sabado': es_sabado
            })
            
            fecha_iteracion += timedelta(days=1)
        
        return {
            'success': True,
            'empleada': {
                'id': str(empleada.id),
                'nombre': empleada.nombre,
                'apellido': empleada.apellido,
                'nombre_completo': f"{empleada.nombre} {empleada.apellido}"
            },
            'calendario': calendario
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener disponibilidad: {str(e)}"
        )


@router.get("/horarios/{plan_id}/{fecha}")
async def get_horarios_disponibles(
    plan_id: str,
    fecha: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene los horarios disponibles para un plan en una fecha específica
    """
    try:
        plan_repo = PlanRepository(db)
        plan = plan_repo.get_by_id(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Parsear la fecha
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )
        
        # Verificar si es sábado
        es_sabado = fecha_obj.weekday() == 5
        
        # Obtener configuración de horarios del plan
        hora_inicio_plan = plan.hora_inicio if plan.hora_inicio else time(6, 0)  # 6:00 AM por defecto
        hora_final_plan = plan.hora_final if plan.hora_final else time(18, 0)  # 6:00 PM por defecto
        horas_servicio = plan.horas_servicio if plan.horas_servicio else 4
        
        # Generar slots de horarios
        horarios_disponibles = []
        
        inicio_minutos = hora_inicio_plan.hour * 60 + hora_inicio_plan.minute
        final_minutos = hora_final_plan.hour * 60 + hora_final_plan.minute
        duracion_servicio_minutos = horas_servicio * 60
        
        slot_actual = inicio_minutos
        while slot_actual + duracion_servicio_minutos <= final_minutos:
            hora_inicio_slot = time(slot_actual // 60, slot_actual % 60)
            hora_final_slot = time(
                (slot_actual + duracion_servicio_minutos) // 60,
                (slot_actual + duracion_servicio_minutos) % 60
            )
            
            # Calcular sobrecargo para sábados después del mediodía
            sobrecargo = 0
            if es_sabado and hora_final_slot > time(12, 0):
                sobrecargo = 10000
            
            horarios_disponibles.append({
                'hora_inicio': hora_inicio_slot.strftime('%H:%M'),
                'hora_final': hora_final_slot.strftime('%H:%M'),
                'horas_duracion': horas_servicio,
                'sobrecargo_sabado': sobrecargo,
                'descripcion': f"{hora_inicio_slot.strftime('%H:%M')} - {hora_final_slot.strftime('%H:%M')} ({horas_servicio}h)"
            })
            
            slot_actual += 30
        
        return {
            'success': True,
            'plan': {
                'id': str(plan.id),
                'nombre': plan.nombre,
                'hora_inicio_disponible': hora_inicio_plan.strftime('%H:%M'),
                'hora_final_disponible': hora_final_plan.strftime('%H:%M'),
                'horas_servicio': horas_servicio
            },
            'fecha': fecha,
            'es_sabado': es_sabado,
            'horarios_disponibles': horarios_disponibles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener horarios: {str(e)}"
        )


@router.get("/planes/{plan_id}/tareas-extra")
async def get_tareas_extra(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene las tareas extra disponibles para un plan
    (tareas que no están incluidas en el plan)
    """
    try:
        plan_repo = PlanRepository(db)
        plan = plan_repo.get_by_id(plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Lista completa de todas las tareas posibles
        todas_las_tareas = [
            'Limpieza de pisos',
            'Limpieza de baños',
            'Limpieza de cocina',
            'Limpieza de ventanas',
            'Limpieza de muebles',
            'Aspirado',
            'Trapeado',
            'Desempolvado',
            'Limpieza de electrodomésticos',
            'Organización de espacios',
            'Limpieza de persianas',
            'Limpieza de espejos',
            'Cambio de sábanas',
            'Lavado de vajilla',
            'Limpieza de alfombras'
        ]
        
        # Obtener servicios incluidos en el plan
        servicios_incluidos = []
        if hasattr(plan, 'servicios_asociados') and plan.servicios_asociados:
            servicios_incluidos = plan.servicios_asociados if isinstance(plan.servicios_asociados, list) else []
        
        # Filtrar tareas extra (las que no están incluidas)
        tareas_extra = []
        for tarea in todas_las_tareas:
            if tarea not in servicios_incluidos:
                tareas_extra.append({
                    'nombre': tarea,
                    'precio': 15000  # Precio fijo por tarea extra
                })
        
        return {
            'success': True,
            'tareas_extra': tareas_extra,
            'plan': {
                'id': str(plan.id),
                'nombre': plan.nombre,
                'servicios_incluidos': servicios_incluidos
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tareas extra: {str(e)}"
        )


@router.post("/calcular-precio")
async def calcular_precio(
    request: CalculoPrecioRequest,
    db: Session = Depends(get_db)
):
    """
    Calcula el precio total de una reserva antes de crearla
    """
    try:
        plan_repo = PlanRepository(db)
        plan = plan_repo.get_by_id(request.plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        # Precio base del plan por día
        precio_plan = float(plan.precio) if plan.precio else 0
        cantidad_dias = len(request.fechas_horarios)
        
        # Calcular precio base (sin descuentos)
        precio_base = precio_plan * cantidad_dias
        
        # Calcular tareas extra
        precio_tarea_extra = 15000
        total_tareas_extra = len(request.tareas_extra) * precio_tarea_extra * cantidad_dias
        
        # Calcular sobrecargos de sábado
        total_sobrecargos = sum(fh.sobrecargo_sabado for fh in request.fechas_horarios)
        
        # Subtotal (antes del descuento)
        subtotal = precio_base + total_tareas_extra + total_sobrecargos
        
        # Calcular descuento por cantidad de días
        porcentaje_descuento = 0
        if cantidad_dias <= 3:
            porcentaje_descuento = 0
        elif cantidad_dias <= 7:
            porcentaje_descuento = 3
        elif cantidad_dias <= 11:
            porcentaje_descuento = 5
        elif cantidad_dias <= 14:
            porcentaje_descuento = 7
        else:
            porcentaje_descuento = 10
        
        # Aplicar descuento
        descuento_dias = subtotal * (porcentaje_descuento / 100)
        precio_final = subtotal - descuento_dias
        
        # Precio por día
        precio_por_dia = precio_final / cantidad_dias if cantidad_dias > 0 else 0
        
        return {
            'success': True,
            'calculo': {
                'precio_base': precio_base,
                'cantidad_dias': cantidad_dias,
                'cantidad_tareas_extra': len(request.tareas_extra),
                'precio_tareas_extra': total_tareas_extra,
                'sobrecargo_sabados': total_sobrecargos,
                'pisos_extra': 0,
                'precio_pisos_extra': 0,
                'subtotal': subtotal,
                'porcentaje_descuento_dias': porcentaje_descuento,
                'descuento_dias': descuento_dias,
                'precio_final': precio_final,
                'precio_por_dia': precio_por_dia
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular precio: {str(e)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular precio: {str(e)}"
        )


@router.post("/crear")
async def crear_reservas(
    request: CrearReservasRequest,
    db: Session = Depends(get_db)
):
    """
    Crea múltiples reservas para las fechas seleccionadas
    """
    try:
        # Verificar que todos los recursos existen
        usuario_repo = UsuarioRepository(db)
        plan_repo = PlanRepository(db)
        ubicacion_repo = UbicacionRepository(db)
        
        empleada = usuario_repo.get_by_id(request.empleada_id)
        if not empleada or empleada.rol != "empleada":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleada no encontrada"
            )
        
        plan = plan_repo.get_by_id(request.plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan no encontrado"
            )
        
        ubicacion = ubicacion_repo.get_by_id(request.ubicacion_id)
        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )
        
        # Calcular precio total
        precio_plan = float(plan.precio)
        cantidad_dias = len(request.fechas_horarios)
        
        porcentaje_descuento = 0
        if cantidad_dias <= 3:
            porcentaje_descuento = 0
        elif cantidad_dias <= 7:
            porcentaje_descuento = 3
        elif cantidad_dias <= 11:
            porcentaje_descuento = 5
        elif cantidad_dias <= 14:
            porcentaje_descuento = 7
        else:
            porcentaje_descuento = 10
        
        subtotal_plan = precio_plan * cantidad_dias
        descuento_dias = subtotal_plan * (porcentaje_descuento / 100)
        total_plan = subtotal_plan - descuento_dias
        
        total_sobrecargos = sum(fh.sobrecargo_sabado for fh in request.fechas_horarios)
        total_tareas_extra = len(request.tareas_extra) * 15000 * cantidad_dias
        precio_total = total_plan + total_sobrecargos + total_tareas_extra
        
        # Crear las reservas usando el modelo correcto
        reserva_repo = ReservaRepository(db)
        reservas_creadas = []
        
        # Convertir IDs string a UUID
        from uuid import UUID
        empleada_uuid = UUID(request.empleada_id)
        plan_uuid = UUID(request.plan_id)
        ubicacion_uuid = UUID(request.ubicacion_id)
        usuario_uuid = ubicacion.id_usuario  # Cliente de la ubicación
        
        for fecha_horario in request.fechas_horarios:
            fecha_obj = datetime.strptime(fecha_horario.fecha, '%Y-%m-%d').date()
            
            # Calcular precio individual para esta fecha
            precio_individual = precio_plan + fecha_horario.sobrecargo_sabado
            if request.tareas_extra:
                precio_individual += len(request.tareas_extra) * 15000
            
            # Aplicar descuento proporcional
            precio_individual -= (precio_individual * porcentaje_descuento / 100)
            
            reserva_data = ReservaCreate(
                id_usuario=usuario_uuid,
                id_empleada=empleada_uuid,
                id_plan=plan_uuid,
                id_lugar=ubicacion_uuid,
                fecha=fecha_obj,
                hora_inicio=datetime.strptime(fecha_horario.hora_inicio, '%H:%M').time(),
                hora_final=datetime.strptime(fecha_horario.hora_final, '%H:%M').time(),
                estado='programada',
                precio_total=precio_individual,
                descripcion=f"Tareas extra: {', '.join(request.tareas_extra)}" if request.tareas_extra else None
            )
            
            reserva = reserva_repo.create(reserva_data)
            reservas_creadas.append(reserva)
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Se crearon {len(reservas_creadas)} reservas exitosamente',
            'data': {
                'reservas_creadas': len(reservas_creadas),
                'fechas': [fh.fecha for fh in request.fechas_horarios],
                'resumen': {
                    'precio_total': precio_total,
                    'cantidad_dias': cantidad_dias,
                    'descuento_aplicado': porcentaje_descuento
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear reservas: {str(e)}"
        )
