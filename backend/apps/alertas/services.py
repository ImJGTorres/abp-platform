import logging
from datetime import date
from django.db import transaction, IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_modelo(ruta):
    from django.apps import apps as django_apps
    app_label, model_name = ruta.rsplit('.', 1)
    return django_apps.get_model(app_label, model_name)


def _crear_alerta(tipo, usuario_id, mensaje, proyecto_id=None, referencia_id=None):
    from apps.alertas.models import Alerta
    try:
        with transaction.atomic():
            Alerta.objects.create(
                tipo=tipo,
                id_usuario_destino_id=usuario_id,
                id_proyecto_id=proyecto_id,
                mensaje=mensaje,
                referencia_id=referencia_id,
            )
        return True
    except IntegrityError:
        return False


def generar_alertas_actividades_vencidas():
    # Actividad está en la app 'cursos' (apps.cursos)
    Actividad = _get_modelo('cursos.Actividad')
    MiembroEquipo = _get_modelo('equipos.MiembroEquipo')

    hoy = date.today()
    actividades_vencidas = Actividad.objects.filter(
        fecha_limite__lt=hoy,
        estado__in=['pendiente', 'en_progreso'],
    ).select_related(
        'id_fase__id_proyecto__id_curso',
        'id_responsable',
        'id_equipo_asignado',
    ).prefetch_related('responsables')

    creadas = 0
    for act in actividades_vencidas:
        proyecto = act.id_fase.id_proyecto
        curso = proyecto.id_curso

        usuarios_destino = set()
        if act.id_responsable_id:
            usuarios_destino.add(act.id_responsable_id)
        # Responsables M2M (pueden asignarse desde el frontend)
        responsables_m2m = act.responsables.values_list('id', flat=True)
        usuarios_destino.update(responsables_m2m)
        if act.id_equipo_asignado_id:
            miembros = MiembroEquipo.objects.filter(
                equipo_id=act.id_equipo_asignado_id,
                estado='activo',
            ).values_list('usuario_id', flat=True)
            usuarios_destino.update(miembros)

        if curso.id_docente_id:
            usuarios_destino.add(curso.id_docente_id)

        dias_retraso = (hoy - act.fecha_limite).days
        mensaje = (
            f"La actividad '{act.nombre}' venció hace {dias_retraso} día(s) "
            f"(límite: {act.fecha_limite}) en el proyecto '{proyecto.nombre}' "
            f"y aún no está completada."
        )

        for uid in usuarios_destino:
            ok = _crear_alerta(
                tipo='actividad_vencida',
                usuario_id=uid,
                mensaje=mensaje,
                proyecto_id=proyecto.id,
                referencia_id=act.id,
            )
            if ok:
                creadas += 1

    return creadas


def generar_alertas_entregables_pendientes():
    # Entregable estados: borrador, enviado, aprobado, rechazado
    # 'borrador' = nunca enviado (equivale a pendiente de envío)
    Entregable = _get_modelo('entregables.Entregable')
    MiembroEquipo = _get_modelo('equipos.MiembroEquipo')

    hoy = date.today()
    entregables_pendientes = Entregable.objects.filter(
        estado='borrador',
        id_actividad__fecha_limite__lt=hoy,
    ).select_related(
        'id_actividad__id_fase__id_proyecto__id_curso',
        'id_equipo',
    )

    creadas = 0
    for ent in entregables_pendientes:
        proyecto = ent.id_actividad.id_fase.id_proyecto
        curso = proyecto.id_curso

        miembros = MiembroEquipo.objects.filter(
            equipo_id=ent.id_equipo_id,
            estado='activo',
        ).values_list('usuario_id', flat=True)

        usuarios_destino = set(miembros)
        if curso.id_docente_id:
            usuarios_destino.add(curso.id_docente_id)

        dias = (hoy - ent.id_actividad.fecha_limite).days
        mensaje = (
            f"El entregable '{ent.titulo}' del proyecto '{proyecto.nombre}' "
            f"sigue sin enviarse con {dias} día(s) de retraso."
        )

        for uid in usuarios_destino:
            ok = _crear_alerta(
                tipo='entregable_pendiente',
                usuario_id=uid,
                mensaje=mensaje,
                proyecto_id=proyecto.id,
                referencia_id=ent.id,
            )
            if ok:
                creadas += 1

    return creadas


def ejecutar_generacion_completa():
    from apps.bitacora.models import BitacoraSistema

    resultados = {}
    try:
        resultados['actividades_vencidas'] = generar_alertas_actividades_vencidas()
    except Exception as e:
        logger.error(f"Error generando alertas actividades vencidas: {e}")
        resultados['actividades_vencidas'] = 0

    try:
        resultados['entregables_pendientes'] = generar_alertas_entregables_pendientes()
    except Exception as e:
        logger.error(f"Error generando alertas entregables pendientes: {e}")
        resultados['entregables_pendientes'] = 0

    total = sum(resultados.values())

    try:
        BitacoraSistema.objects.create(
            nombre_usuario='sistema',
            accion='CREATE',
            modulo='alertas',
            descripcion=(
                f"Generación automática de alertas. Total nuevas: {total}. "
                f"Detalle: {resultados}"
            ),
        )
    except Exception as e:
        logger.warning(f"No se pudo registrar en bitácora la generación de alertas: {e}")

    return resultados
