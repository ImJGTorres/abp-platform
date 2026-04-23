import secrets
import string
import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def generar_contrasena(longitud=10):
    caracteres = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


def enviar_contrasena_bienvenida(nombre, email, contrasena):
    asunto = "Bienvenido a la Plataforma ABP — Tus credenciales de acceso"
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Tu cuenta ha sido creada en la Plataforma ABP.\n\n"
        f"Correo: {email}\n"
        f"Contraseña temporal: {contrasena}\n\n"
        f"Por seguridad, cambia tu contraseña al iniciar sesión.\n\n"
        f"— Equipo ABP UFPS"
    )
    send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
