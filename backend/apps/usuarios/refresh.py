from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch
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
        datos = super().validate(attrs)
        if 'refresh' in datos:
            # La rotación de simplejwt no registra el refresh nuevo en OutstandingToken:
            # sin registro, cerrar_todas_las_sesiones no lo revoca al cambiar la contraseña.
            nuevo = RefreshToken(datos['refresh'])
            OutstandingToken.objects.get_or_create(
                jti=nuevo['jti'],
                defaults={
                    'user': usuario,
                    'token': datos['refresh'],
                    'created_at': nuevo.current_time,
                    'expires_at': datetime_from_epoch(nuevo['exp']),
                },
            )
        return datos


class RefreshActivoView(TokenRefreshView):
    """POST /api/auth/refresh/"""
    serializer_class = RefreshActivoSerializer
