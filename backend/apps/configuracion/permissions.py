from rest_framework.permissions import BasePermission

from apps.usuarios.permissions import EsAdministrador  # noqa: F401  (re-exportado)
# BasePermission: Clase base de Django REST Framework para crear permisos personalizados


class IsAdminOrDocente(BasePermission):
    """
    Permiso personalizado que permite acceso a usuarios administradores o docentes.
    
    Se usa en endpoints GET de períodos académicos donde tanto administradores
    como docentes pueden ver la lista de períodos.
    """
    
    message = 'Se requiere rol de administrador o docente.'

    def has_permission(self, request, view):
        usuario = getattr(request, 'usuario', None) or getattr(request, 'user', None)
        if usuario is None:
            return False
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        return tipo_rol in ('administrador', 'docente')