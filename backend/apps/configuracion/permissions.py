from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """
    Permite el acceso solo si request.user existe
    y tiene tipo_rol == 'administrador'.
    """
    message = 'Se requiere rol de administrador.'

    def has_permission(self, request, view):
        usuario = getattr(request, 'user', None)
        return (
            usuario is not None
            and getattr(usuario, 'tipo_rol', None) == 'administrador'
        )
