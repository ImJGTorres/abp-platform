from rest_framework.permissions import BasePermission

from apps.usuarios.models import Usuario


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