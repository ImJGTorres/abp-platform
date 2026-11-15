"""Límite de intentos fallidos de login (protección contra fuerza bruta).

Tres contadores en la caché de Django, todos con la misma ventana:
- par (correo, IP): bloquea a quien insiste sobre una cuenta desde una IP.
- correo: tope más alto; frena ataques repartidos entre muchas IP sin dejar que un
  tercero bloquee la cuenta con solo 5 intentos desde su propia IP.
- IP: frena el rociado de contraseñas sobre muchos correos.
Superado cualquiera, el login responde 429 hasta que termina la ventana. Un login correcto
reinicia el contador del par.

La caché por defecto es LocMem (por proceso): con varios workers el límite efectivo es por
worker. Con una caché compartida (Redis) pasa a ser global sin cambiar este código.
"""
from django.conf import settings
from django.core.cache import cache

from apps.bitacora.utils import _get_ip


def _claves(request, correo):
    correo = (correo or '').strip().lower()
    ip = _get_ip(request) or 'desconocida'
    return (
        (f'login_fallos:par:{correo}:{ip}', settings.LOGIN_MAX_INTENTOS_PAR),
        (f'login_fallos:correo:{correo}', settings.LOGIN_MAX_INTENTOS_CORREO),
        (f'login_fallos:ip:{ip}', settings.LOGIN_MAX_INTENTOS_IP),
    )


def login_bloqueado(request, correo):
    return any(cache.get(clave, 0) >= maximo for clave, maximo in _claves(request, correo))


def registrar_fallo_login(request, correo):
    for clave, _ in _claves(request, correo):
        # add() fija la ventana al primer fallo; incr() no la renueva
        cache.add(clave, 0, settings.LOGIN_VENTANA_SEGUNDOS)
        try:
            cache.incr(clave)
        except ValueError:  # expiró entre add() e incr()
            cache.set(clave, 1, settings.LOGIN_VENTANA_SEGUNDOS)


def limpiar_fallos_login(request, correo):
    cache.delete(_claves(request, correo)[0][0])
