"""Regla única de acceso a los reportes, usada por la API de reportes y por las exportaciones.

- administrador y director: ven todo (indicadores y tendencia solo ellos).
- docente: solo cursos, proyectos, equipos y estudiantes de sus propios cursos.
- estudiante / líder: solo su propio reporte y solo en proyectos donde es miembro activo.

Si el recurso no existe, se devuelve True para que la vista responda 404 (no 403).
"""
from apps.cursos.models import Curso, CursoEstudiante, Proyecto
from apps.equipos.models import Equipo, MiembroEquipo

ROLES_DIRECTOR = ('director', 'docente', 'administrador')
ROLES_INDICADORES = ('director', 'administrador')
ROLES_ESTUDIANTE = ('estudiante', 'lider_equipo')
ROLES_GLOBALES = ('director', 'administrador')


def _id(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def docente_es_dueno_de_curso(usuario, curso_id):
    curso = Curso.objects.filter(pk=_id(curso_id)).only('id_docente_id').first()
    return curso is None or curso.id_docente_id == usuario.pk


def docente_es_dueno_de_proyecto(usuario, proyecto_id):
    proyecto = Proyecto.objects.filter(pk=_id(proyecto_id)).select_related('id_curso').first()
    return proyecto is None or proyecto.id_curso.id_docente_id == usuario.pk


def docente_es_dueno_de_equipo(usuario, equipo_id):
    equipo = Equipo.objects.filter(pk=_id(equipo_id)).select_related('proyecto__id_curso').first()
    return equipo is None or equipo.proyecto.id_curso.id_docente_id == usuario.pk


def docente_tiene_estudiante(usuario, estudiante_id):
    """El estudiante está inscrito en un curso del docente o es miembro de un proyecto suyo."""
    return (
        CursoEstudiante.objects.filter(
            estudiante_id=estudiante_id, curso__id_docente=usuario, estado='activo'
        ).exists()
        or MiembroEquipo.objects.filter(
            usuario_id=estudiante_id, equipo__proyecto__id_curso__id_docente=usuario
        ).exists()
    )


def estudiante_es_miembro_de_proyecto(usuario_id, proyecto_id):
    return MiembroEquipo.objects.filter(
        usuario_id=usuario_id, equipo__proyecto_id=_id(proyecto_id), estado='activo'
    ).exists()


def puede_ver_reporte(usuario, tipo_reporte, parametros=None):
    """True si el usuario puede consultar (o exportar) el reporte indicado.

    tipo_reporte: proyecto | equipo | curso | estudiante | indicadores | tendencia.
    parametros: proyecto_id / equipo_id / curso_id / estudiante_id según el tipo.
    """
    parametros = parametros or {}
    rol = getattr(usuario, 'tipo_rol', None)

    if tipo_reporte in ('indicadores', 'tendencia'):
        return rol in ROLES_INDICADORES
    if rol in ROLES_GLOBALES:
        return tipo_reporte in ('proyecto', 'equipo', 'curso', 'estudiante')

    if rol == 'docente':
        if tipo_reporte == 'proyecto':
            return docente_es_dueno_de_proyecto(usuario, parametros.get('proyecto_id'))
        if tipo_reporte == 'equipo':
            return docente_es_dueno_de_equipo(usuario, parametros.get('equipo_id'))
        if tipo_reporte == 'curso':
            return docente_es_dueno_de_curso(usuario, parametros.get('curso_id'))
        if tipo_reporte == 'estudiante':
            if parametros.get('proyecto_id') is not None:
                return docente_es_dueno_de_proyecto(usuario, parametros.get('proyecto_id'))
            return docente_tiene_estudiante(usuario, _id(parametros.get('estudiante_id')))
        return False

    if rol in ROLES_ESTUDIANTE and tipo_reporte == 'estudiante':
        if _id(parametros.get('estudiante_id')) != usuario.pk:
            return False
        proyecto_id = parametros.get('proyecto_id')
        return proyecto_id is None or estudiante_es_miembro_de_proyecto(usuario.pk, proyecto_id)
    return False
