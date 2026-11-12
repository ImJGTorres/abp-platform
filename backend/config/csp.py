"""Content-Security-Policy para el frontend servido por Django (NUE-13).

Los tokens JWT viven en localStorage, así que la mitigación principal ante XSS es no
ejecutar scripts ajenos: script-src solo 'self'. /django-admin/ queda fuera porque el
admin de Django usa scripts en línea. Fuera de DEBUG se activa; el HMR de Vite en
desarrollo necesita scripts en línea y por eso no se aplica allí.
"""
from django.conf import settings

POLITICA = '; '.join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' data: https://fonts.gstatic.com",
    "img-src 'self' data: blob:{extra}",
    "connect-src 'self'{extra}",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "form-action 'self'",
])


class CSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            settings.CSP_ENABLED
            and not request.path.startswith('/django-admin/')
            and 'Content-Security-Policy' not in response
        ):
            extra = ''.join(f' {origen}' for origen in settings.CSP_CONNECT_SRC_EXTRA)
            response['Content-Security-Policy'] = POLITICA.format(extra=extra)
        return response
