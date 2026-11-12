"""Propiedad de cursos y proyectos: una sola regla para docentes (usada por varias apps)."""


def es_dueno_o_admin(usuario, curso):
    """True si es administrador o el docente dueño del curso."""
    rol = getattr(usuario, 'tipo_rol', None)
    if rol == 'administrador':
        return True
    return rol == 'docente' and curso.id_docente_id == usuario.pk


def puede_gestionar_proyecto(usuario, proyecto):
    """Administrador o docente dueño del curso del proyecto."""
    return es_dueno_o_admin(usuario, proyecto.id_curso)


def puede_ver_proyecto(usuario, proyecto):
    """Lectura: admin, director, docente dueño, miembro activo de un equipo o estudiante inscrito."""
    from apps.cursos.models import CursoEstudiante
    from apps.equipos.models import MiembroEquipo

    rol = getattr(usuario, 'tipo_rol', None)
    if rol in ('administrador', 'director'):
        return True
    if rol == 'docente':
        return proyecto.id_curso.id_docente_id == usuario.pk
    return (
        MiembroEquipo.objects.filter(usuario=usuario, equipo__proyecto=proyecto, estado='activo').exists()
        or CursoEstudiante.objects.filter(
            estudiante=usuario, curso_id=proyecto.id_curso_id, estado='activo').exists()
    )
