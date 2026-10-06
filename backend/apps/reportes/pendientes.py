"""
Pendientes priorizados del usuario para la pantalla de inicio (HU-038).

Cada pendiente: {tipo, titulo, fecha, urgencia, enlace}
  tipo     -- vencido | proximo | sin_calificar | alerta
  urgencia -- 3 (más urgente) a 1
  enlace   -- ruta del frontend a la que lleva el pendiente
"""
from datetime import date, timedelta

from django.db.models import Q

DIAS_PROXIMO = 3


def _pendiente(tipo, titulo, fecha, urgencia, enlace):
    if hasattr(fecha, 'date'):  # datetime -> date
        fecha = fecha.date()
    return {'tipo': tipo, 'titulo': titulo, 'fecha': fecha, 'urgencia': urgencia, 'enlace': enlace}


def _alertas_no_leidas(usuario, enlace_proyecto):
    from apps.alertas.models import Alerta

    alertas = Alerta.objects.filter(id_usuario_destino=usuario, estado='no_leida')
    return [
        _pendiente('alerta', a.mensaje, a.fecha_generacion, 1,
                   enlace_proyecto(a.id_proyecto_id) if a.id_proyecto_id else None)
        for a in alertas
    ]


def _pendientes_estudiante(usuario, hoy):
    from apps.cursos.models import Actividad
    from apps.entregables.models import Entregable
    from apps.equipos.models import MiembroEquipo

    equipo_ids = list(MiembroEquipo.objects.filter(usuario=usuario, estado='activo')
                      .values_list('equipo_id', flat=True))
    actividades = (
        Actividad.objects
        .filter(Q(id_responsable=usuario) | Q(responsables=usuario) | Q(id_equipo_asignado_id__in=equipo_ids))
        .exclude(estado='completada')
        .filter(fecha_limite__lte=hoy + timedelta(days=DIAS_PROXIMO))
        .select_related('id_fase')
        .distinct()
    )
    pendientes = []
    for act in actividades:
        enlace = f'/estudiante/proyectos/{act.id_fase.id_proyecto_id}/actividades'
        if act.fecha_limite < hoy:
            pendientes.append(_pendiente('vencido', f"Actividad vencida: {act.nombre}",
                                         act.fecha_limite, 3, enlace))
        else:
            pendientes.append(_pendiente('proximo', f"Actividad por vencer: {act.nombre}",
                                         act.fecha_limite, 2, enlace))

    entregables = (Entregable.objects
                   .filter(id_equipo_id__in=equipo_ids, estado__in=('borrador', 'rechazado'))
                   .select_related('id_actividad__id_fase'))
    for ent in entregables:
        act = ent.id_actividad
        accion = 'corregir' if ent.estado == 'rechazado' else 'enviar'
        pendientes.append(_pendiente(
            'proximo', f"Entregable por {accion}: {ent.titulo}",
            act.fecha_limite if act else ent.fecha_creacion, 2,
            f'/estudiante/proyectos/{act.id_fase.id_proyecto_id}/actividades/{act.id}/entregables' if act else None,
        ))

    return pendientes + _alertas_no_leidas(usuario, lambda p: f'/estudiante/proyectos/{p}')


def _pendientes_docente(usuario, hoy):
    from apps.cursos.models import Actividad
    from apps.entregables.models import Entregable

    def enlace_actividad(act, sufijo=''):
        return (f'/docente/proyectos/{act.id_fase.id_proyecto_id}/fases/{act.id_fase_id}'
                f'/actividades/{act.id}{sufijo}')

    pendientes = []
    sin_calificar = (
        Entregable.objects
        .filter(estado='enviado', id_actividad__id_fase__id_proyecto__id_curso__id_docente=usuario)
        .exclude(evaluaciones__estado='publicada')
        .select_related('id_actividad__id_fase', 'id_equipo')
    )
    for ent in sin_calificar:
        pendientes.append(_pendiente(
            'sin_calificar', f"Entregable sin calificar: {ent.titulo} ({ent.id_equipo.nombre})",
            ent.fecha_envio or ent.fecha_creacion, 3, enlace_actividad(ent.id_actividad, '/entregables'),
        ))

    vencidas = (
        Actividad.objects
        .filter(id_fase__id_proyecto__id_curso__id_docente=usuario, fecha_limite__lt=hoy)
        .exclude(estado='completada')
        .select_related('id_fase')
    )
    for act in vencidas:
        pendientes.append(_pendiente('vencido', f"Actividad vencida: {act.nombre}",
                                     act.fecha_limite, 2, enlace_actividad(act)))

    return pendientes + _alertas_no_leidas(usuario, lambda p: f'/docente/proyectos/{p}/monitoreo')


def _pendientes_director(usuario, hoy):
    from apps.configuracion.models import PeriodoAcademico
    from .services import get_estudiantes_bajo_rendimiento

    pendientes = _alertas_no_leidas(usuario, lambda p: f'/director/reportes/proyecto/{p}')

    # ponytail: recorre los estudiantes del periodo activo; si se vuelve lento, cachear el conteo.
    periodo = PeriodoAcademico.objects.filter(estado='activo').values_list('id', flat=True).first()
    rojos = len(get_estudiantes_bajo_rendimiento(periodo_id=periodo, solo_riesgo=True))
    if rojos:
        pendientes.append(_pendiente('alerta', f"{rojos} estudiante(s) en rojo (riesgo crítico)",
                                     hoy, 2, '/director/riesgo'))
    return pendientes


_POR_ROL = {
    'estudiante': _pendientes_estudiante,
    'lider_equipo': _pendientes_estudiante,
    'docente': _pendientes_docente,
    'director': _pendientes_director,
    'administrador': _pendientes_director,
}


def pendientes_usuario(usuario):
    """Pendientes del usuario según su rol, ordenados por urgencia desc y fecha asc."""
    hoy = date.today()
    calcular = _POR_ROL.get(usuario.tipo_rol)
    pendientes = calcular(usuario, hoy) if calcular else []
    pendientes.sort(key=lambda p: (-p['urgencia'], p['fecha'] or date.max))

    resumen = {'total': len(pendientes), 'vencido': 0, 'proximo': 0, 'sin_calificar': 0, 'alerta': 0}
    for p in pendientes:
        resumen[p['tipo']] += 1
    return {'al_dia': not pendientes, 'pendientes': pendientes, 'resumen': resumen}
