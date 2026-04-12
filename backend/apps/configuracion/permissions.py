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
        """
        Verifica si el usuario tiene permisos de administrador.
        
        Args:
            request: Objeto HTTP request de Django REST Framework
            view: Vista que está siendo accedida
            
        Returns:
            bool: True si el usuario es administrador, False en caso contrario
            
        Proceso:
            1. Obtiene el objeto 'usuario' del request (añadido por autenticación JWT)
            2. Verifica que exista el usuario
            3. Verifica que el tipo_rol del usuario sea 'administrador'
        """
        # request.usuario es añadido por el middleware/authentication de JWT
        # Contiene el usuario autenticado del modelo Usuario
        usuario = getattr(request, 'usuario', None)
        
        # Retorna True solo si:
        # - El usuario existe (no es None)
        # - El tipo_rol del usuario es exactamente 'administrador'
        return (
            usuario is not None
            and getattr(usuario, 'tipo_rol', None) == 'administrador'
        )