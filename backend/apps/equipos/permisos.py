"""Autorización para operaciones de escritura sobre equipos.

Una sola regla (rol + propiedad) que usan todas las vistas de gestión de equipos:
administrador y director, o el docente dueño del curso del proyecto.
"""
from rest_framework.exceptions import PermissionDenied

from apps.usuarios.models import Usuario


def puede_gestionar_proyecto(usuario, proyecto):
    """True si el usuario puede crear/editar/disolver equipos y sus miembros."""
    if getattr(usuario, 'tipo_rol', None) in (
        Usuario.TipoRol.ADMINISTRADOR,
        Usuario.TipoRol.DIRECTOR,
    ):
        return True
    return (
        getattr(usuario, 'tipo_rol', None) == Usuario.TipoRol.DOCENTE
        and proyecto.id_curso.id_docente_id == usuario.pk
    )


def exigir_gestion_proyecto(usuario, proyecto):
    """Lanza 403 si el usuario no puede gestionar los equipos del proyecto."""
    if not puede_gestionar_proyecto(usuario, proyecto):
        raise PermissionDenied('No tienes permiso para gestionar los equipos de este proyecto.')
