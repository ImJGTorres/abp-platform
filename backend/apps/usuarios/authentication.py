from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.usuarios.models import Usuario


# UsuarioJWTAuthentication: Autenticador JWT personalizado (BE-02 Extra)
# Extiende JWTAuthentication de SimpleJWT para usar el modelo Usuario
# en lugar del modelo auth.User de Django por defecto.
#
# Diferencia con autenticador por defecto:
# - auth.User: Busca usuario por ID en tabla auth_user
# - Usuario: Busca usuario por user_id enNuestro modelo personalizado
class UsuarioJWTAuthentication(JWTAuthentication):
    """
    Autenticador JWT que resuelve el token al modelo Usuario personalizado
    en lugar del auth.User de Django.
    """

    def get_user(self, validated_token):
        """
        Extrae el usuario del token JWT personalizado.
        
        Proceso:
        1. Extrae user_id del payload del token (no del sub estándar)
        2. Busca en modelo Usuario personalizado
        3. Verifica que esté activo
        4. Retorna instancia de Usuario para usar en request.user
        """
        # Extrae user_id del token (personalizado en LoginView línea 59)
        # El token tiene user_id, no sub estándar de Django
        user_id = validated_token.get('user_id')
        
        # Valida que el token contenga user_id
        if user_id is None:
            raise InvalidToken('El token no contiene user_id.')
        
        # Busca usuario en nuestro modelo personalizado
        # Tabla: apps_usuarios_usuario (no auth_user)
        try:
            usuario = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            raise InvalidToken('Usuario no encontrado.')
        
        # Verifica estado activo del usuario (seguridad)
        # Usuarios inactivos no pueden autenticarse
        if usuario.estado != Usuario.Estado.ACTIVO:
            raise InvalidToken('Usuario inactivo.')
        
        # Retorna usuario para usar en request.user
        # Permite usar @authentication_classes en views
        return usuario