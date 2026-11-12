import ipaddress
import logging

from django.conf import settings

from .models import BitacoraSistema

logger = logging.getLogger(__name__)


def _ip_valida(valor):
    try:
        return str(ipaddress.ip_address((valor or '').strip()))
    except ValueError:
        return None


def _get_ip(request):
    """IP del cliente, a prueba de X-Forwarded-For falsificado.

    El cliente puede mandar su propio X-Forwarded-For; cada proxy de confianza agrega la IP
    que él ve al FINAL de la lista. Por eso se toma la entrada que está TRUSTED_PROXY_COUNT
    posiciones desde el final (1 = un proxy, Render). Un valor que no sea IP se descarta y se
    usa REMOTE_ADDR, así tampoco se rompe el INSERT de la bitácora (campo inet).

    Args:
        request: Objeto HttpRequest de Django.

    Returns:
        str | None: Dirección IP del cliente, o None si no se puede determinar.
    """
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        entradas = [e.strip() for e in forwarded_for.split(',') if e.strip()]
        n = max(1, int(getattr(settings, 'TRUSTED_PROXY_COUNT', 1)))
        if len(entradas) >= n:
            ip = _ip_valida(entradas[-n])
            if ip:
                return ip
    return _ip_valida(request.META.get('REMOTE_ADDR'))


def registrar_evento(request, accion, modulo, descripcion=None):
    """Registra un evento en la bitácora del sistema.

    Si la creación del registro falla por cualquier motivo (error de BD, datos
    inválidos, etc.), el error se captura y se loggea con nivel ERROR sin
    propagar la excepción. Esto garantiza que un fallo de auditoría nunca
    interrumpa la respuesta HTTP principal.

    Uso:
        registrar_evento(request, BitacoraSistema.Accion.LOGIN, 'autenticacion', 'Login exitoso')

    Args:
        request:     HttpRequest de Django. Puede ser None para acciones del sistema
                     sin contexto de solicitud HTTP.
        accion:      Valor de BitacoraSistema.Accion que clasifica el tipo de evento.
        modulo:      Nombre del módulo que genera el evento (ej. 'equipos', 'usuarios').
        descripcion: Texto libre opcional con detalle adicional del evento.

    Returns:
        BitacoraSistema | None: El objeto creado, o None si la creación falló.
    """
    usuario = None
    nombre_usuario = 'sistema'
    ip_origen = None

    if request is not None:
        ip_origen = _get_ip(request)
        # Soporta tanto request.usuario (login manual) como request.user (JWT)
        user = getattr(request, 'usuario', None) or getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            usuario = user
            nombre_usuario = f'{user.nombre} {user.apellido}'

    try:
        return BitacoraSistema.objects.create(
            id_usuario=usuario,
            nombre_usuario=nombre_usuario,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip_origen=ip_origen,
        )
    except Exception:
        logger.exception(
            "Error al registrar evento en bitácora: accion=%s, modulo=%s, descripcion=%s",
            accion,
            modulo,
            descripcion,
        )
        return None