from rest_framework.permissions import BasePermission

from apps.roles.models import Permiso, Rol, RolPermiso
from apps.usuarios.models import Usuario


def TienePermiso(codigo_permiso):
    """
    Factory que retorna una clase de permiso DRF.
    Verifica si el rol del usuario tiene el permiso específico.
    """

    class TienePermisoClass(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            if not user or not isinstance(user, Usuario) or not user.tipo_rol:
                return False

            return RolPermiso.objects.filter(
                rol__nombre__iexact=user.tipo_rol,
                permiso__codigo=codigo_permiso
            ).exists()

    return TienePermisoClass


class EsAdministrador(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'administrador'."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user is not None
            and isinstance(user, Usuario)
            and user.tipo_rol == Usuario.TipoRol.ADMINISTRADOR
            and user.estado == Usuario.Estado.ACTIVO
        )


class EsDocente(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'docente'."""

    def has_permission(self, request, view):
        user = request.user
        return (
            user is not None
            and isinstance(user, Usuario)
            and user.tipo_rol == Usuario.TipoRol.DOCENTE
            and user.estado == Usuario.Estado.ACTIVO
        )
