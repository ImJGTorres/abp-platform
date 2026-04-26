from rest_framework.permissions import BasePermission


class EsDocente(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'docente'."""

    message = 'Se requiere rol de docente.'

    def has_permission(self, request, view):
        usuario = request.user
        return (
            usuario is not None
            and usuario.is_authenticated
            and getattr(usuario, 'tipo_rol', None) == 'docente'
        )


class EsAdministrador(BasePermission):
    """Permite acceso solo a usuarios con tipo_rol == 'administrador'."""

    message = 'Se requiere rol de administrador.'

    def has_permission(self, request, view):
        usuario = request.user
        return (
            usuario is not None
            and usuario.is_authenticated
            and getattr(usuario, 'tipo_rol', None) == 'administrador'
        )


class EsDocenteOAdministrador(BasePermission):
    """Permite acceso a docentes y administradores."""

    message = 'Se requiere rol de docente o administrador.'

    def has_permission(self, request, view):
        usuario = request.user
        return (
            usuario is not None
            and usuario.is_authenticated
            and getattr(usuario, 'tipo_rol', None) in ('docente', 'administrador')
        )