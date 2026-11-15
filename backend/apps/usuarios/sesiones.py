from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


def cerrar_todas_las_sesiones(usuario):
    """Pone en lista negra todos los refresh tokens vigentes del usuario.

    Se usa al cambiar o recuperar la contraseña: las sesiones abiertas no deben sobrevivir.
    Los access tokens ya emitidos caducan solos (1 h).
    """
    for token in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=token)
