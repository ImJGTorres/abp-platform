from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.usuarios.models import Usuario


class RefreshActivoSerializer(TokenRefreshSerializer):
    """Refresca el token solo si el usuario sigue activo (el refresh estándar no lo comprueba)."""

    def validate(self, attrs):
        try:
            user_id = RefreshToken(attrs['refresh']).get('user_id')
        except TokenError as exc:
            raise InvalidToken(exc.args[0])
        usuario = Usuario.objects.filter(pk=user_id).first()
        if usuario is None or usuario.estado != Usuario.Estado.ACTIVO:
            raise InvalidToken('Usuario inactivo.')
        return super().validate(attrs)


class RefreshActivoView(TokenRefreshView):
    """POST /api/auth/refresh/"""
    serializer_class = RefreshActivoSerializer
