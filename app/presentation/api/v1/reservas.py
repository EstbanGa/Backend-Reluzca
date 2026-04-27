from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta, time
from app.presentation.dependencies import get_db, get_current_user, require_role
from app.infrastructure.repositories.reserva_repository import ReservaRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.ubicacion_repository import UbicacionRepository
from app.infrastructure.repositories.notificacion_repository import NotificacionRepository
from app.infrastructure.repositories.actividad_repository import ActividadRepository
from app.application.services.reserva_service import ReservaService
from app.domain.schemas.reserva import ReservaCreate, ReservaUpdate, ReservaResponse, ReservasWithStatsResponse
from app.domain.models.usuario import Usuario
from pydantic import BaseModel

router = APIRouter(prefix="/reservas", tags=["reservas"])


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


@router.get("/empleada/{empleada_id}/detalle")
def get_reservas_by_empleada_detalle(
    empleada_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtiene reservas de una empleada con datos completos de cliente, plan y ubicación."""
    if current_user.id != empleada_id and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver estas reservas",
        )
    svc = ReservaService(ReservaRepository(db), UsuarioRepository(db), PlanRepository(db), UbicacionRepository(db))
    return svc.get_reservas_by_empleada_with_stats(empleada_id)


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


@router.get("/empleadas/{empleada_id}/disponibilidad")
def get_disponibilidad_empleada(
    empleada_id: str,
    dias: int = Query(60, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Retorna el calendario de disponibilidad de una empleada para los próximos N días.
    Permite múltiples servicios por día — un día se marca como 'ocupado' solo si ya tiene
    2 o más reservas activas. Un día con 1 reserva sigue apareciendo como disponible
    para que el cliente pueda agendar un segundo servicio en horario diferente.
    """
    try:
        from app.domain.models.reserva import Reserva as ReservaModel
        from datetime import timedelta, date as date_type
        import calendar as cal_module

        hoy = date_type.today()

        # Obtener reservas futuras de la empleada (estados activos)
        reservas = (
            db.query(ReservaModel)
            .filter(
                ReservaModel.id_empleada == empleada_id,
                ReservaModel.fecha >= hoy,
                ReservaModel.estado.in_(['programada', 'confirmada', 'en_proceso', 'pendiente'])
            )
            .all()
        )

        # Índice: fecha → cantidad de reservas
        reservas_por_dia: dict = {}
        for r in reservas:
            key = r.fecha.isoformat() if r.fecha else None
            if key:
                reservas_por_dia[key] = reservas_por_dia.get(key, 0) + 1

        calendario = []
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        for i in range(dias):
            fecha = hoy + timedelta(days=i)
            fecha_str = fecha.isoformat()
            dia_num = fecha.weekday()  # 0=lunes ... 6=domingo
            es_domingo = dia_num == 6
            es_sabado = dia_num == 5
            count = reservas_por_dia.get(fecha_str, 0)
            # Disponible si: no es domingo, no es pasado, y tiene menos de 2 reservas
            disponible = not es_domingo and count < 2

            calendario.append({
                "fecha": fecha_str,
                "disponible": disponible,
                "dia_semana": dias_semana[dia_num],
                "es_hoy": fecha == hoy,
                "es_pasado": False,  # solo fechas futuras
                "es_sabado": es_sabado,
                "es_domingo": es_domingo,
                "sobrecargo_sabado": es_sabado,
                "reservas_existentes": count
            })

        return {"success": True, "calendario": calendario}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener disponibilidad: {str(e)}"
        )


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
                    "horas_servicio": plan.horas_servicio if hasattr(plan, 'horas_servicio') and plan.horas_servicio else 4,
                    "hora_inicio": plan.hora_inicio.strftime('%H:%M') if hasattr(plan, 'hora_inicio') and plan.hora_inicio else None,
                    "hora_final": plan.hora_final.strftime('%H:%M') if hasattr(plan, 'hora_final') and plan.hora_final else None,
                    "tipo_plan": plan.tipo_plan if hasattr(plan, 'tipo_plan') else "full",
                    "servicios_asociados": plan.servicios_asociados if hasattr(plan, 'servicios_asociados') and plan.servicios_asociados else [],
                    "actividades": [
                        {
                            "id": str(a.id),
                            "nombre": a.nombre,
                            "precio_unitario": float(a.precio_unitario) if hasattr(a, 'precio_unitario') and a.precio_unitario else None,
                        }
                        for a in (plan.actividades if hasattr(plan, 'actividades') and plan.actividades else [])
                    ]
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
    plan_id: Optional[str] = None
    ubicacion_id: str
    fechas_horarios: List[FechaHorario]
    tareas_extra: List[str] = []
    actividades_seleccionadas: List[str] = []


class CrearReservasRequest(BaseModel):
    empleada_id: str
    plan_id: Optional[str] = None
    ubicacion_id: str
    fechas_horarios: List[FechaHorario]
    tareas_extra: List[str] = []
    actividades_seleccionadas: List[str] = []


# (duplicate /empleadas/{empleada_id}/disponibilidad removed – first registration is canonical)


@router.get("/horarios/{plan_id}/{fecha}")
async def get_horarios_disponibles(
    plan_id: str,
    fecha: str,
    empleada_id: Optional[str] = Query(None, description="UUID de la empleada para filtrar slots ocupados"),
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
        # Horario laboral: 7am – 7pm
        HORA_INICIO_LABORAL = time(7, 0)
        HORA_FIN_LABORAL = time(19, 0)

        # Respetar horario laboral sobreescribiendo el plan si excede límites
        hora_inicio_plan = max(hora_inicio_plan, HORA_INICIO_LABORAL)
        hora_final_plan = min(hora_final_plan, HORA_FIN_LABORAL)

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

        # Filtrar slots que conflictúan con reservas existentes de la empleada
        if empleada_id:
            try:
                from app.domain.models.reserva import Reserva as ReservaModel
                from uuid import UUID as UUIDType

                emp_uuid = UUIDType(empleada_id)
                reservas_dia = (
                    db.query(ReservaModel)
                    .filter(
                        ReservaModel.id_empleada == emp_uuid,
                        ReservaModel.fecha == fecha_obj,
                        ReservaModel.estado.in_(['programada', 'confirmada', 'en_proceso', 'pendiente'])
                    )
                    .all()
                )

                def slot_tiene_conflicto(s_ini: time, s_fin: time) -> bool:
                    """True si el slot viola el gap de 1 hora con alguna reserva existente."""
                    dt_base = datetime(2000, 1, 1)
                    si = datetime.combine(dt_base.date(), s_ini)
                    sf = datetime.combine(dt_base.date(), s_fin)
                    gap = timedelta(hours=1)
                    for r in reservas_dia:
                        ri = datetime.combine(dt_base.date(), r.hora_inicio)
                        rf = datetime.combine(dt_base.date(), r.hora_final)
                        # Conflicto: no hay 1h antes ni 1h después
                        if not (sf <= ri - gap or si >= rf + gap):
                            return True
                    return False

                horarios_disponibles = [
                    h for h in horarios_disponibles
                    if not slot_tiene_conflicto(
                        time(*[int(x) for x in h['hora_inicio'].split(':')]),
                        time(*[int(x) for x in h['hora_final'].split(':')])
                    )
                ]
            except Exception:
                pass  # No filtrar si falla
        
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
                    'precio': 15  # Precio fijo por tarea extra
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
        cantidad_dias = len(request.fechas_horarios)
        if cantidad_dias == 0:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos una fecha")

        # --- Precio del plan (si aplica) ---
        precio_plan = 0.0
        if request.plan_id:
            plan_repo = PlanRepository(db)
            plan = plan_repo.get_by_id(request.plan_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
            precio_plan = float(plan.precio) if plan.precio else 0

        precio_base_plan = precio_plan * cantidad_dias

        # --- Precio de actividades individuales (si aplica) ---
        precio_actividades_unitario = 0.0
        if request.actividades_seleccionadas:
            act_repo = ActividadRepository(db)
            for act_id in request.actividades_seleccionadas:
                actividad = act_repo.get_by_id(act_id)
                if actividad and actividad.precio_unitario:
                    precio_actividades_unitario += float(actividad.precio_unitario)

        precio_actividades_total = precio_actividades_unitario * cantidad_dias

        # Precio base combinado
        precio_base = precio_base_plan + precio_actividades_total

        # --- Tareas extra (solo cuando hay plan) ---
        precio_tarea_extra = 15
        total_tareas_extra = len(request.tareas_extra) * precio_tarea_extra * cantidad_dias if request.plan_id else 0

        # --- Sobrecargos de sábado ---
        total_sobrecargos = sum(fh.sobrecargo_sabado for fh in request.fechas_horarios)

        # Subtotal (antes del descuento)
        subtotal = precio_base + total_tareas_extra + total_sobrecargos

        # Descuento por cantidad de días
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

        descuento_dias = subtotal * (porcentaje_descuento / 100)
        precio_final = subtotal - descuento_dias
        precio_por_dia = precio_final / cantidad_dias if cantidad_dias > 0 else 0

        return {
            'success': True,
            'calculo': {
                'precio_plan_unitario': precio_plan,
                'precio_base_plan': precio_base_plan,
                'precio_actividades_unitario': precio_actividades_unitario,
                'precio_actividades': precio_actividades_total,
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
        
        plan = None
        precio_plan = 0.0
        if request.plan_id:
            plan = plan_repo.get_by_id(request.plan_id)
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan no encontrado"
                )
            precio_plan = float(plan.precio) if plan.precio else 0
        
        ubicacion = ubicacion_repo.get_by_id(request.ubicacion_id)
        if not ubicacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ubicación no encontrada"
            )

        # Precio de actividades individuales
        precio_actividades_unitario = 0.0
        if request.actividades_seleccionadas:
            act_repo = ActividadRepository(db)
            for act_id in request.actividades_seleccionadas:
                actividad = act_repo.get_by_id(act_id)
                if actividad and actividad.precio_unitario:
                    precio_actividades_unitario += float(actividad.precio_unitario)
        
        # Calcular precio total
        cantidad_dias = len(request.fechas_horarios)
        precio_unitario_dia = precio_plan + precio_actividades_unitario
        
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
        
        subtotal_base = precio_unitario_dia * cantidad_dias
        descuento_dias = subtotal_base * (porcentaje_descuento / 100)
        total_base = subtotal_base - descuento_dias
        
        total_sobrecargos = sum(fh.sobrecargo_sabado for fh in request.fechas_horarios)
        total_tareas_extra = len(request.tareas_extra) * 15 * cantidad_dias if request.plan_id else 0
        precio_total = total_base + total_sobrecargos + total_tareas_extra
        
        # Crear las reservas usando el modelo correcto
        reserva_repo = ReservaRepository(db)
        reservas_creadas = []
        
        # Convertir IDs string a UUID
        from uuid import UUID
        empleada_uuid = UUID(request.empleada_id)
        plan_uuid = UUID(request.plan_id) if request.plan_id else None
        ubicacion_uuid = UUID(request.ubicacion_id)
        usuario_uuid = ubicacion.id_usuario  # Cliente de la ubicación
        
        # ── Validación de horario laboral (7am-7pm) y gap de 1 hora ──────────
        HORA_INICIO_LABORAL = time(7, 0)
        HORA_FIN_LABORAL = time(19, 0)
        GAP_MINIMO = timedelta(hours=1)
        ESTADOS_ACTIVOS = ['programada', 'confirmada', 'en_proceso', 'pendiente']

        from app.domain.models.reserva import Reserva as ReservaModel

        for fh in request.fechas_horarios:
            fh_inicio = datetime.strptime(fh.hora_inicio, '%H:%M').time()
            fh_final = datetime.strptime(fh.hora_final, '%H:%M').time()
            fh_fecha = datetime.strptime(fh.fecha, '%Y-%m-%d').date()

            if fh_inicio < HORA_INICIO_LABORAL or fh_final > HORA_FIN_LABORAL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El servicio del {fh.fecha} ({fh.hora_inicio}–{fh.hora_final}) debe estar dentro del horario laboral (07:00–19:00)"
                )

            reservas_dia = (
                db.query(ReservaModel)
                .filter(
                    ReservaModel.id_empleada == empleada_uuid,
                    ReservaModel.fecha == fh_fecha,
                    ReservaModel.estado.in_(ESTADOS_ACTIVOS)
                )
                .all()
            )

            dt_base = datetime(2000, 1, 1)
            si_new = datetime.combine(dt_base.date(), fh_inicio)
            sf_new = datetime.combine(dt_base.date(), fh_final)

            for r in reservas_dia:
                si_r = datetime.combine(dt_base.date(), r.hora_inicio)
                sf_r = datetime.combine(dt_base.date(), r.hora_final)
                if not (sf_new <= si_r - GAP_MINIMO or si_new >= sf_r + GAP_MINIMO):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"La reserva del {fh.fecha} ({fh.hora_inicio}–{fh.hora_final}) no cumple la separación mínima de 1 hora con otra reserva existente ({r.hora_inicio.strftime('%H:%M')}–{r.hora_final.strftime('%H:%M')})"
                    )
        # ─────────────────────────────────────────────────────────────────────

        for fecha_horario in request.fechas_horarios:
            fecha_obj = datetime.strptime(fecha_horario.fecha, '%Y-%m-%d').date()
            
            # Calcular precio individual para esta fecha
            precio_individual = precio_unitario_dia + fecha_horario.sobrecargo_sabado
            if request.plan_id and request.tareas_extra:
                precio_individual += len(request.tareas_extra) * 15
            
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

        # Notificar a la empleada sobre las nuevas reservas asignadas
        try:
            notif_repo = NotificacionRepository(db)
            n = len(reservas_creadas)
            fechas_str = ", ".join(fh.fecha for fh in request.fechas_horarios[:3])
            if n > 3:
                fechas_str += f" y {n - 3} más"
            notif_repo.create(
                id_usuario_destino=empleada_uuid,
                tipo="reserva",
                mensaje=f"Se te asignaron {n} nueva(s) reserva(s) para las fechas: {fechas_str}.",
                canal="in_app",
            )
        except Exception:
            pass  # No fallar si la notificación falla

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


# ─────────────────────────────────────────────────────────────────────────────
# CHECKLIST DE ACTIVIDADES POR RESERVA (Items 14/15)
# ─────────────────────────────────────────────────────────────────────────────

class SetActividadesReservaRequest(BaseModel):
    actividad_ids: List[str]
    programada: bool = True


class ToggleActividadRequest(BaseModel):
    ejecutada: bool
    notas: Optional[str] = None


@router.get("/{reserva_id}/actividades")
def get_actividades_reserva(reserva_id: UUID, db: Session = Depends(get_db)):
    """Obtiene la lista de actividades (checklist) de una reserva."""
    from app.domain.models.reserva_actividad import ReservaActividad
    from app.domain.models.actividad import Actividad
    items = (
        db.query(ReservaActividad)
        .filter(ReservaActividad.id_reserva == reserva_id)
        .all()
    )
    result = []
    for item in items:
        actividad = db.query(Actividad).filter(Actividad.id == item.id_actividad).first()
        result.append({
            "id": str(item.id),
            "id_actividad": str(item.id_actividad),
            "nombre": actividad.nombre if actividad else "?",
            "precio_unitario": float(actividad.precio_unitario) if actividad and actividad.precio_unitario else None,
            "duracion_estimada_minutos": actividad.duracion_estimada_minutos if actividad else None,
            "programada": item.programada,
            "ejecutada": item.ejecutada,
            "notas": item.notas,
        })
    return {"actividades": result}


@router.post("/{reserva_id}/actividades")
def set_actividades_reserva(
    reserva_id: UUID,
    data: SetActividadesReservaRequest,
    db: Session = Depends(get_db),
):
    """Establece el checklist de actividades de una reserva (reemplaza el existente)."""
    from app.domain.models.reserva_actividad import ReservaActividad
    import uuid as uuid_lib
    # Eliminar existentes
    db.query(ReservaActividad).filter(ReservaActividad.id_reserva == reserva_id).delete()
    # Crear nuevos
    for act_id in data.actividad_ids:
        item = ReservaActividad(
            id=uuid_lib.uuid4(),
            id_reserva=reserva_id,
            id_actividad=uuid_lib.UUID(act_id),
            programada=data.programada,
            ejecutada=False,
        )
        db.add(item)
    db.commit()
    return {"success": True, "message": f"{len(data.actividad_ids)} actividades asignadas"}


@router.patch("/{reserva_id}/actividades/{item_id}/toggle")
def toggle_actividad_ejecutada(
    reserva_id: UUID,
    item_id: UUID,
    data: ToggleActividadRequest,
    db: Session = Depends(get_db),
):
    """Marca una actividad como ejecutada o no ejecutada."""
    from app.domain.models.reserva_actividad import ReservaActividad
    item = db.query(ReservaActividad).filter(
        ReservaActividad.id == item_id,
        ReservaActividad.id_reserva == reserva_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    item.ejecutada = data.ejecutada
    if data.notas is not None:
        item.notas = data.notas
    db.commit()
    return {"success": True, "ejecutada": item.ejecutada}


# ─────────────────────────────────────────────────────────────────────────────
# FOTOS DEL SERVICIO (Item 14)
# ─────────────────────────────────────────────────────────────────────────────

class AddFotoRequest(BaseModel):
    url_foto: str  # base64 data URL o URL en la nube
    descripcion: Optional[str] = None
    tipo: str = "durante"  # antes, durante, despues
    id_actividad: Optional[str] = None  # UUID del ítem en reservas_actividades
    subida_por: Optional[str] = None


@router.get("/{reserva_id}/fotos")
def get_fotos_reserva(reserva_id: UUID, db: Session = Depends(get_db)):
    """Obtiene las fotos de una reserva."""
    from app.domain.models.foto_servicio import FotoServicio
    fotos = db.query(FotoServicio).filter(FotoServicio.id_reserva == reserva_id).all()
    return {
        "fotos": [
            {
                "id": str(f.id),
                "url_foto": f.url_foto,
                "descripcion": f.descripcion,
                "tipo": f.tipo,
                "id_actividad": str(f.id_actividad) if f.id_actividad else None,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in fotos
        ]
    }


@router.post("/{reserva_id}/fotos", status_code=status.HTTP_201_CREATED)
def add_foto_reserva(
    reserva_id: UUID,
    data: AddFotoRequest,
    db: Session = Depends(get_db),
):
    """Registra una foto (base64 o URL) en la reserva. id_actividad la asocia a una actividad concreta."""
    from app.domain.models.foto_servicio import FotoServicio
    import uuid as uuid_lib
    foto = FotoServicio(
        id=uuid_lib.uuid4(),
        id_reserva=reserva_id,
        url_foto=data.url_foto,
        descripcion=data.descripcion,
        tipo=data.tipo,
        id_actividad=uuid_lib.UUID(data.id_actividad) if data.id_actividad else None,
        subida_por=uuid_lib.UUID(data.subida_por) if data.subida_por else None,
    )
    db.add(foto)
    db.commit()
    return {
        "id": str(foto.id),
        "url_foto": foto.url_foto,
        "tipo": foto.tipo,
        "id_actividad": str(foto.id_actividad) if foto.id_actividad else None,
    }


@router.delete("/{reserva_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_foto_reserva(
    reserva_id: UUID,
    foto_id: UUID,
    db: Session = Depends(get_db),
):
    """Elimina una foto de una reserva."""
    from app.domain.models.foto_servicio import FotoServicio
    foto = db.query(FotoServicio).filter(
        FotoServicio.id == foto_id,
        FotoServicio.id_reserva == reserva_id,
    ).first()
    if foto:
        db.delete(foto)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# GANANCIAS EMPLEADA (Items 16/17)
# ─────────────────────────────────────────────────────────────────────────────

PORCENTAJE_EMPLEADA = 0.60  # 60% del precio total va a la empleada


@router.get("/empleada/{empleada_id}/ganancias")
def get_ganancias_empleada(
    empleada_id: UUID,
    mes: Optional[str] = Query(None, description="YYYY-MM, por defecto mes actual"),
    db: Session = Depends(get_db),
):
    """
    Calcula las ganancias de una empleada en un período mensual.
    Por defecto devuelve el mes actual + los 5 meses anteriores como histórico.
    """
    from app.domain.models.reserva import Reserva as ReservaModel
    from app.domain.models.plan import Plan as PlanModel
    from datetime import date as date_type
    import calendar as cal_module

    hoy = date_type.today()

    # Determinar mes objetivo
    if mes:
        try:
            anio, mes_num = int(mes[:4]), int(mes[5:7])
        except Exception:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Use YYYY-MM")
    else:
        anio, mes_num = hoy.year, hoy.month

    primer_dia = date_type(anio, mes_num, 1)
    ultimo_dia_num = cal_module.monthrange(anio, mes_num)[1]
    ultimo_dia = date_type(anio, mes_num, ultimo_dia_num)

    # Reservas completadas del mes
    reservas_mes = (
        db.query(ReservaModel)
        .filter(
            ReservaModel.id_empleada == empleada_id,
            ReservaModel.estado == "completada",
            ReservaModel.fecha >= primer_dia,
            ReservaModel.fecha <= ultimo_dia,
        )
        .all()
    )

    total_bruto = sum(float(r.precio_total or 0) for r in reservas_mes)
    total_neto = total_bruto * PORCENTAJE_EMPLEADA

    detalle = []
    for r in reservas_mes:
        bruto = float(r.precio_total or 0)
        detalle.append({
            "id_reserva": str(r.id),
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "precio_total": bruto,
            "ganancia": round(bruto * PORCENTAJE_EMPLEADA, 2),
        })

    # Histórico: últimos 6 meses
    historico = []
    for i in range(6):
        m = mes_num - i
        a = anio
        while m <= 0:
            m += 12
            a -= 1
        p1 = date_type(a, m, 1)
        p2 = date_type(a, m, cal_module.monthrange(a, m)[1])
        total_h = (
            db.query(ReservaModel)
            .filter(
                ReservaModel.id_empleada == empleada_id,
                ReservaModel.estado == "completada",
                ReservaModel.fecha >= p1,
                ReservaModel.fecha <= p2,
            )
            .count()
        )
        bruto_h = sum(
            float(r.precio_total or 0)
            for r in db.query(ReservaModel)
            .filter(
                ReservaModel.id_empleada == empleada_id,
                ReservaModel.estado == "completada",
                ReservaModel.fecha >= p1,
                ReservaModel.fecha <= p2,
            )
            .all()
        )
        historico.append({
            "mes": f"{a}-{m:02d}",
            "total_servicios": total_h,
            "total_bruto": round(bruto_h, 2),
            "total_neto": round(bruto_h * PORCENTAJE_EMPLEADA, 2),
        })

    return {
        "empleada_id": str(empleada_id),
        "mes": f"{anio}-{mes_num:02d}",
        "resumen": {
            "total_servicios": len(reservas_mes),
            "total_bruto": round(total_bruto, 2),
            "total_neto": round(total_neto, 2),
            "porcentaje_empleada": int(PORCENTAJE_EMPLEADA * 100),
        },
        "detalle": detalle,
        "historico": historico,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESERVA ACTIVA DE LA EMPLEADA (panel "En Progreso" tipo Rappi)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/empleada/{empleada_id}/activa")
def get_reserva_activa_empleada(
    empleada_id: str,
    db: Session = Depends(get_db),
):
    """
    Retorna la reserva que actualmente está en proceso para una empleada.
    Si no hay ninguna 'en_proceso', busca la próxima 'programada' o 'confirmada' para hoy.
    Incluye datos del cliente, plan, ubicación, checklist y fotos.
    """
    from app.domain.models.reserva import Reserva as ReservaModel
    from app.domain.models.usuario import Usuario as UsuarioModel
    from app.domain.models.plan import Plan as PlanModel
    from app.domain.models.ubicacion import UbicacionServicio
    from app.domain.models.reserva_actividad import ReservaActividad
    from app.domain.models.actividad import Actividad
    from app.domain.models.foto_servicio import FotoServicio
    from datetime import date as date_type
    import uuid as uuid_lib

    try:
        emp_uuid = uuid_lib.UUID(empleada_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de empleada inválido")

    hoy = date_type.today()

    # 1. Reserva en_curso / en_proceso (primera prioridad)
    reserva = (
        db.query(ReservaModel)
        .filter(
            ReservaModel.id_empleada == emp_uuid,
            ReservaModel.estado.in_(["en_curso", "en_proceso"]),
        )
        .order_by(ReservaModel.fecha.desc(), ReservaModel.hora_inicio.asc())
        .first()
    )

    # 2. Reserva de hoy programada / confirmada / pendiente (segunda prioridad)
    if not reserva:
        reserva = (
            db.query(ReservaModel)
            .filter(
                ReservaModel.id_empleada == emp_uuid,
                ReservaModel.fecha == hoy,
                ReservaModel.estado.in_(["programada", "confirmada", "pendiente"]),
            )
            .order_by(ReservaModel.hora_inicio.asc())
            .first()
        )

    if not reserva:
        return {"activa": False, "reserva": None}

    # Datos relacionados
    cliente = db.query(UsuarioModel).filter(UsuarioModel.id == reserva.id_usuario).first()
    plan = db.query(PlanModel).filter(PlanModel.id == reserva.id_plan).first() if reserva.id_plan else None
    lugar = db.query(UbicacionServicio).filter(UbicacionServicio.id == reserva.id_lugar).first() if reserva.id_lugar else None

    # Checklist de actividades
    items = (
        db.query(ReservaActividad)
        .filter(ReservaActividad.id_reserva == reserva.id)
        .all()
    )
    actividades = []
    for item in items:
        act = db.query(Actividad).filter(Actividad.id == item.id_actividad).first()
        actividades.append({
            "id": str(item.id),
            "id_actividad": str(item.id_actividad),
            "nombre": act.nombre if act else "?",
            "descripcion": act.descripcion if act else None,
            "duracion_estimada_minutos": act.duracion_estimada_minutos if act else None,
            "programada": item.programada,
            "ejecutada": item.ejecutada,
            "notas": item.notas,
        })

    # Fotos
    fotos = db.query(FotoServicio).filter(FotoServicio.id_reserva == reserva.id).all()
    fotos_data = [
        {
            "id": str(f.id),
            "url_foto": f.url_foto,
            "tipo": f.tipo,
            "descripcion": f.descripcion,
            "id_actividad": str(f.id_actividad) if f.id_actividad else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in fotos
    ]

    return {
        "activa": True,
        "reserva": {
            "id": str(reserva.id),
            "fecha": reserva.fecha.isoformat() if reserva.fecha else None,
            "hora_inicio": reserva.hora_inicio.strftime("%H:%M") if reserva.hora_inicio else None,
            "hora_final": reserva.hora_final.strftime("%H:%M") if reserva.hora_final else None,
            "estado": reserva.estado,
            "precio_total": float(reserva.precio_total) if reserva.precio_total else None,
            "descripcion": reserva.descripcion,
            "cliente": {
                "id": str(cliente.id),
                "nombre": f"{cliente.nombre} {cliente.apellido}",
                "telefono": cliente.telefono,
                "correo": cliente.correo,
            } if cliente else None,
            "plan": {
                "id": str(plan.id),
                "nombre": plan.nombre,
                "descripcion": plan.descripcion,
            } if plan else None,
            "lugar": {
                "id": str(lugar.id),
                "nombre": lugar.nombre,
                "nombre_lugar": lugar.nombre_lugar,
                "tipo_lugar": lugar.tipo_lugar,
                "descripcion": lugar.descripcion,
            } if lugar else None,
            "actividades": actividades,
            "fotos": fotos_data,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETAR / INICIAR RESERVA (empleada)
# ─────────────────────────────────────────────────────────────────────────────

class UpdateEstadoReservaRequest(BaseModel):
    estado: str  # en_proceso, completada, etc.


@router.patch("/{reserva_id}/estado")
def update_estado_reserva(
    reserva_id: UUID,
    data: UpdateEstadoReservaRequest,
    db: Session = Depends(get_db),
):
    """Cambia el estado de una reserva (empleada puede iniciar o completar)."""
    from app.domain.models.reserva import Reserva as ReservaModel
    reserva = db.query(ReservaModel).filter(ReservaModel.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    reserva.estado = data.estado
    db.commit()

    # Notificar al cliente y a la empleada sobre el cambio de estado
    try:
        notif_repo = NotificacionRepository(db)
        msgs_cliente = {
            "confirmada": "Tu reserva ha sido confirmada. ¡Te esperamos!",
            "en_proceso": "El servicio de tu reserva ha comenzado.",
            "completada": "Tu reserva ha sido completada. ¡Gracias por confiar en Reluzca!",
            "cancelada": "Tu reserva ha sido cancelada. Contáctanos si tienes dudas.",
            "pendiente": "Tu reserva ha vuelto a estado pendiente.",
        }
        msgs_empleada = {
            "confirmada": "Una reserva asignada a ti ha sido confirmada.",
            "en_proceso": "Una reserva asignada a ti está ahora en proceso.",
            "completada": "Una reserva asignada a ti ha sido marcada como completada.",
            "cancelada": "Una reserva asignada a ti ha sido cancelada.",
        }
        rid = UUID(str(reserva.id))
        msg_c = msgs_cliente.get(data.estado, f"El estado de tu reserva cambió a: {data.estado}.")
        notif_repo.create(
            id_usuario_destino=UUID(str(reserva.id_usuario)),
            tipo="reserva",
            mensaje=msg_c,
            canal="in_app",
            id_reserva=rid,
        )
        if reserva.id_empleada and data.estado in msgs_empleada:
            notif_repo.create(
                id_usuario_destino=UUID(str(reserva.id_empleada)),
                tipo="reserva",
                mensaje=msgs_empleada[data.estado],
                canal="in_app",
                id_reserva=rid,
            )
    except Exception:
        pass  # No fallar si la notificación falla

    return {"success": True, "id": str(reserva.id), "estado": reserva.estado}

