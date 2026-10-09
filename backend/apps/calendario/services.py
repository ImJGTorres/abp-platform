"""
Calendario unificado (HU-040): hitos, entregas, revisiones y fechas límite de
actividades de los proyectos del usuario, en una sola lista.
"""
from datetime import date, timedelta

from django.db.models import Q

ROLES_EQUIPO = ('estudiante', 'lider_equipo')
ROLES_GLOBALES = ('director', 'administrador')

URGENCIA_VENCIDO = 'vencido'
URGENCIA_PROXIMO = 'proximo'
URGENCIA_NORMAL = 'normal'

ESTADOS_HITO_CERRADO = ('completado', 'cancelado')


def proyectos_usuario(usuario):
    """
    Proyectos visibles para el usuario según su rol:
      estudiante / lider_equipo -> proyectos donde tiene membresía activa en un equipo;
      docente                   -> proyectos de los cursos que dicta (Curso.id_docente);
      director / administrador  -> todos los proyectos no finalizados.
    """
    from apps.cursos.models import Proyecto

    if usuario.tipo_rol in ROLES_EQUIPO:
        return Proyecto.objects.filter(
            equipos__miembros__usuario=usuario,
            equipos__miembros__estado='activo',
        ).distinct()
    if usuario.tipo_rol == 'docente':
        return Proyecto.objects.filter(id_curso__id_docente=usuario)
    if usuario.tipo_rol in ROLES_GLOBALES:
        return Proyecto.objects.exclude(estado=Proyecto.Estado.FINALIZADO)
    return Proyecto.objects.none()


def actividades_usuario(usuario, proyectos):
    """Actividades de los proyectos; el estudiante/líder solo ve las suyas o las de su equipo."""
    from apps.cursos.models import Actividad
    from apps.equipos.models import MiembroEquipo

    qs = Actividad.objects.filter(id_fase__id_proyecto__in=proyectos)
    if usuario.tipo_rol in ROLES_EQUIPO:
        equipos = MiembroEquipo.objects.filter(usuario=usuario, estado='activo').values('equipo_id')
        qs = qs.filter(
            Q(id_responsable=usuario) | Q(responsables=usuario) | Q(id_equipo_asignado__in=equipos)
        ).distinct()
    return qs


def calcular_urgencia(fecha, completado, hoy=None):
    """
    vencido: fecha < hoy y no completado.
    proximo: vence entre hoy y hoy + 2 días (≤ 48 h) y no completado.
    normal:  cualquier otro caso (incluye lo ya completado).
    """
    hoy = hoy or date.today()
    if completado:
        return URGENCIA_NORMAL
    if fecha < hoy:
        return URGENCIA_VENCIDO
    if fecha <= hoy + timedelta(days=2):
        return URGENCIA_PROXIMO
    return URGENCIA_NORMAL


def evento_hito(hito, hoy=None):
    proyecto = hito.id_proyecto
    return {
        'id': f'hito-{hito.id}',
        'tipo': hito.tipo,  # hito | entrega | revision (las "evaluaciones" son revisiones)
        'titulo': hito.nombre,
        'fecha': hito.fecha_fin.isoformat(),
        'urgencia': calcular_urgencia(hito.fecha_fin, hito.estado in ESTADOS_HITO_CERRADO, hoy),
        'proyecto_id': proyecto.id,
        'proyecto_nombre': proyecto.nombre,
        'curso_nombre': proyecto.id_curso.nombre,
    }


def evento_actividad(actividad, hoy=None):
    proyecto = actividad.id_fase.id_proyecto
    return {
        'id': f'actividad-{actividad.id}',
        'tipo': 'actividad',
        'titulo': actividad.nombre,
        'fecha': actividad.fecha_limite.isoformat(),
        'urgencia': calcular_urgencia(actividad.fecha_limite, actividad.estado == 'completada', hoy),
        'proyecto_id': proyecto.id,
        'proyecto_nombre': proyecto.nombre,
        'curso_nombre': proyecto.id_curso.nombre,
    }


def eventos_usuario(usuario, desde, hasta):
    """Eventos del usuario con fecha entre desde y hasta (incluidas), ordenados por fecha."""
    from apps.cursos.models import HitoProyecto

    proyectos = proyectos_usuario(usuario)
    hoy = date.today()

    hitos = HitoProyecto.objects.filter(
        id_proyecto__in=proyectos, fecha_fin__gte=desde, fecha_fin__lte=hasta,
    ).select_related('id_proyecto__id_curso')
    actividades = actividades_usuario(usuario, proyectos).filter(
        fecha_limite__gte=desde, fecha_limite__lte=hasta,
    ).select_related('id_fase__id_proyecto__id_curso')

    eventos = [evento_hito(h, hoy) for h in hitos] + [evento_actividad(a, hoy) for a in actividades]
    eventos.sort(key=lambda e: (e['fecha'], e['id']))
    return eventos


# ── Detalle de evento (SCRUM-530) ──────────────────────────────────────────

def _equipo_dict(equipo):
    if equipo is None:
        return None
    miembros = equipo.miembros.filter(estado='activo').select_related('usuario')
    return {
        'nombre': equipo.nombre,
        'miembros': [f'{m.usuario.nombre} {m.usuario.apellido}'.strip() for m in miembros],
    }


def _equipo_del_usuario(usuario, proyecto):
    from apps.equipos.models import Equipo
    return Equipo.objects.filter(
        proyecto=proyecto, miembros__usuario=usuario, miembros__estado='activo',
    ).first()


def _enlace(usuario, proyecto, actividad=None):
    """Ruta del frontend (router/index.jsx) donde se ve el evento, según el rol."""
    p = proyecto.id
    rol = usuario.tipo_rol
    if rol == 'estudiante':
        if actividad:
            return f'/estudiante/proyectos/{p}/actividades/{actividad.id}/entregables'
        return f'/estudiante/proyectos/{p}/progreso'
    if rol == 'lider_equipo':
        if actividad:
            return f'/lider/actividades/{actividad.id}/entregables'
        return f'/lider/proyectos/{p}/kanban'
    if rol == 'docente':
        if actividad:
            return f'/docente/proyectos/{p}/fases/{actividad.id_fase_id}/actividades/{actividad.id}'
        return f'/docente/proyectos/{p}/cronograma'
    if rol == 'director':
        return f'/director/reportes/proyecto/{p}'
    if rol == 'administrador':
        return f'/admin/cursos/{proyecto.id_curso_id}'
    return None


def detalle_evento(usuario, evento_id):
    """
    Detalle de 'hito-<id>' o 'actividad-<id>' si pertenece a un proyecto del usuario
    (y, para estudiante/líder, si la actividad es suya o de su equipo). None si no.
    """
    from apps.cursos.models import AvanceActividad, HitoProyecto, VistaProgresoProyecto

    tipo, _, id_texto = evento_id.partition('-')
    if tipo not in ('hito', 'actividad') or not id_texto.isdigit():
        return None
    pk = int(id_texto)
    proyectos = proyectos_usuario(usuario)

    if tipo == 'hito':
        hito = HitoProyecto.objects.filter(pk=pk, id_proyecto__in=proyectos).select_related(
            'id_proyecto__id_curso').first()
        if hito is None:
            return None
        proyecto = hito.id_proyecto
        avance = (VistaProgresoProyecto.objects.filter(id_proyecto=proyecto.id)
                  .values_list('porcentaje_progreso', flat=True).first())
        return {
            **evento_hito(hito),
            'descripcion': hito.descripcion,
            'estado': hito.estado,
            'porcentaje_avance': avance if avance is not None else 0,
            'equipo': _equipo_dict(_equipo_del_usuario(usuario, proyecto)),
            'enlace': _enlace(usuario, proyecto),
        }

    actividad = actividades_usuario(usuario, proyectos).filter(pk=pk).select_related(
        'id_fase__id_proyecto__id_curso', 'id_equipo_asignado').first()
    if actividad is None:
        return None
    proyecto = actividad.id_fase.id_proyecto
    ultimo = (AvanceActividad.objects.filter(id_actividad=actividad)
              .order_by('-fecha_registro', '-id')
              .values_list('porcentaje_completado', flat=True).first())
    equipo = actividad.id_equipo_asignado or _equipo_del_usuario(usuario, proyecto)
    return {
        **evento_actividad(actividad),
        'descripcion': actividad.descripcion,
        'estado': actividad.estado,
        'porcentaje_avance': ultimo if ultimo is not None else 0,
        'equipo': _equipo_dict(equipo),
        'enlace': _enlace(usuario, proyecto, actividad),
    }
