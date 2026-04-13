from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from apps.usuarios.models import Usuario


class UsuarioJWTAuthentication(JWTAuthentication):
    """
    Autenticador JWT que resuelve el token al modelo Usuario personalizado
    en lugar del auth.User de Django.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        if user_id is None:
            raise InvalidToken('El token no contiene user_id.')
        try:
            usuario = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            raise InvalidToken('Usuario no encontrado.')
        if usuario.estado != Usuario.Estado.ACTIVO:
            raise InvalidToken('Usuario inactivo.')
        return usuario
