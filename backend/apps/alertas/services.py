import logging
from datetime import date, timedelta
from django.db import transaction, IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_modelo(ruta):
    from django.apps import apps as django_apps
    app_label, model_name = ruta.rsplit('.', 1)
    return django_apps.get_model(app_label, model_name)


GRAVEDAD_POR_TIPO = {
    'actividad_vencida': 'alta',
    'bajo_rendimiento': 'alta',
    'entregable_pendiente': 'media',
}

# Plantilla del correo que se encola con cada alerta nueva (por defecto 'alerta').
PLANTILLA_POR_TIPO = {
    'recordatorio_vencimiento': 'recordatorio',
}


def encolar_correo(usuario_id, asunto, plantilla, contexto):
    """Deja un correo en cola_correo en estado pendiente. El envío real es de HU-043."""
    from apps.alertas.models import ColaCorreo
    return ColaCorreo.objects.create(
        id_usuario_destino_id=usuario_id,
        asunto=asunto,
        plantilla=plantilla,
        contexto=contexto,
    )


def _crear_alerta(tipo, usuario_id, mensaje, proyecto_id=None, referencia_id=None):
    from apps.alertas.models import Alerta
    try:
        with transaction.atomic():
            alerta = Alerta.objects.create(
                tipo=tipo,
                id_usuario_destino_id=usuario_id,
                id_proyecto_id=proyecto_id,
                mensaje=mensaje,
                referencia_id=referencia_id,
                gravedad=GRAVEDAD_POR_TIPO.get(tipo, 'baja'),
            )
            # Solo llega aquí si la alerta es nueva; una duplicada lanza IntegrityError
            encolar_correo(
                usuario_id,
                f"Nueva alerta: {alerta.get_tipo_display()}",
                PLANTILLA_POR_TIPO.get(tipo, 'alerta'),
                {'mensaje': mensaje, 'proyecto_id': proyecto_id},
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


def generar_recordatorios_48h():
    """
    Recordatorio para lo que vence en las próximas 48 h (HU-040, tarea diaria).
    Actividades no completadas con fecha_limite entre hoy y hoy + 2 días: una alerta
    'recordatorio_vencimiento' para el responsable (o, si no tiene, los miembros activos
    del equipo asignado). _crear_alerta encola el correo 'recordatorio' solo si la alerta
    es nueva; la restricción única (tipo, usuario, referencia_id) evita duplicados.
    """
    Actividad = _get_modelo('cursos.Actividad')
    MiembroEquipo = _get_modelo('equipos.MiembroEquipo')

    hoy = date.today()
    proximas = Actividad.objects.filter(
        fecha_limite__gte=hoy,
        fecha_limite__lte=hoy + timedelta(days=2),
    ).exclude(estado='completada').select_related('id_fase__id_proyecto').prefetch_related('responsables')

    creadas = 0
    for act in proximas:
        proyecto = act.id_fase.id_proyecto

        usuarios_destino = set(act.responsables.values_list('id', flat=True))
        if act.id_responsable_id:
            usuarios_destino.add(act.id_responsable_id)
        if not usuarios_destino and act.id_equipo_asignado_id:
            usuarios_destino.update(MiembroEquipo.objects.filter(
                equipo_id=act.id_equipo_asignado_id,
                estado='activo',
            ).values_list('usuario_id', flat=True))

        dias = (act.fecha_limite - hoy).days
        cuando = 'hoy' if dias == 0 else f'en {dias} día(s)'
        mensaje = (
            f"La actividad '{act.nombre}' del proyecto '{proyecto.nombre}' vence {cuando} "
            f"(límite: {act.fecha_limite})."
        )

        for uid in usuarios_destino:
            if _crear_alerta(
                tipo='recordatorio_vencimiento',
                usuario_id=uid,
                mensaje=mensaje,
                proyecto_id=proyecto.id,
                referencia_id=act.id,
            ):
                creadas += 1

    return creadas


MAX_INTENTOS_CORREO = 3


def renderizar_correo(correo):
    """
    HTML de una fila de cola_correo con la plantilla correos/<plantilla>.html (HU-043).
    Contexto: el de la fila + membrete (obtener_identidad, logo con URL absoluta),
    url_base (FRONTEND_URL), destinatario y asunto.
    """
    from django.conf import settings
    from django.template.loader import render_to_string
    from apps.configuracion.identidad import obtener_identidad

    url_base = settings.FRONTEND_URL
    identidad = obtener_identidad()
    logo = identidad['logotipo_url']
    usuario = correo.id_usuario_destino
    contexto = {
        **(correo.contexto or {}),
        'identidad': {
            'nombre_institucion': identidad['nombre_institucion'],
            'programa_academico': identidad['programa_academico'],
            'logo_url': f'{url_base}{logo}' if logo and logo.startswith('/') else logo,
        },
        'url_base': url_base,
        'destinatario': f'{usuario.nombre} {usuario.apellido}'.strip(),
        'asunto': correo.asunto,
    }
    return render_to_string(f'correos/{correo.plantilla}.html', contexto)


def despachar_cola(limite=50):
    """
    Envía los correos pendientes de cola_correo, los más antiguos primero (máx. `limite`).
    Tarea 'correos' del scheduler cada 5 min (RNF28: máximo 15 min).
    Éxito -> estado 'enviado' y fecha_envio. Error -> intentos += 1 y se guarda el error;
    al llegar a MAX_INTENTOS_CORREO queda en 'error'. Un correo fallido no detiene el resto.
    """
    from django.core.exceptions import ValidationError
    from django.core.mail import EmailMultiAlternatives
    from django.core.validators import validate_email
    from django.utils.html import strip_tags
    from apps.alertas.models import ColaCorreo

    pendientes = (ColaCorreo.objects.filter(estado='pendiente')
                  .select_related('id_usuario_destino')
                  .order_by('fecha_creacion', 'id')[:limite])

    resultado = {'enviados': 0, 'fallidos': 0}
    for correo in pendientes:
        try:
            destino = (correo.id_usuario_destino.correo or '').strip()
            try:
                validate_email(destino)
            except ValidationError:
                raise ValueError(f'Destinatario sin correo válido: "{destino}"')
            html = renderizar_correo(correo)
            mensaje = EmailMultiAlternatives(subject=correo.asunto, body=strip_tags(html), to=[destino])
            mensaje.attach_alternative(html, 'text/html')
            mensaje.send()
        except Exception as exc:
            logger.exception('Error enviando correo id=%s', correo.id)
            correo.intentos += 1
            correo.error = str(exc)[:2000]
            if correo.intentos >= MAX_INTENTOS_CORREO:
                correo.estado = 'error'
            correo.save(update_fields=['intentos', 'error', 'estado'])
            resultado['fallidos'] += 1
            continue

        correo.estado = 'enviado'
        correo.fecha_envio = timezone.now()
        correo.error = None
        correo.save(update_fields=['estado', 'fecha_envio', 'error'])
        resultado['enviados'] += 1

    return resultado


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
