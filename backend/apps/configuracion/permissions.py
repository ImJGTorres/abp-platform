from rest_framework.permissions import BasePermission
# BasePermission: Clase base de Django REST Framework para crear permisos personalizados


class EsAdministrador(BasePermission):
    """
    Permiso personalizado que restringe el acceso a usuarios con rol de administrador.
    
    Este permiso se usa en las views de configuración para asegurar que solo
    los usuarios administradores puedan:
    - Consultar todos los parámetros del sistema (GET)
    - Actualizar parámetros específicos (PATCH)
    
    Si un usuario sin rol de administrador intenta acceder, recibe un error 403
    con el mensaje definido en 'message'.
    """
    
    # Mensaje que se retorna cuando el permiso es denegado
    # Se muestra al cliente cuando has_permission retorna False
    message = 'Se requiere rol de administrador.'

    def has_permission(self, request, view):
        usuario = getattr(request, 'usuario', None) or getattr(request, 'user', None)
        return (
            usuario is not None
            and getattr(usuario, 'tipo_rol', None) == 'administrador'
        )