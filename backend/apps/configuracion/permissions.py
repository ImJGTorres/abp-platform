from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """
    Permite el acceso solo si request.usuario existe
    y tiene tipo_rol == 'administrador'.
    """
    message = 'Se requiere rol de administrador.'

    def has_permission(self, request, view):
        usuario = getattr(request, 'usuario', None)
        return (
            usuario is not None
            and getattr(usuario, 'tipo_rol', None) == 'administrador'
        )