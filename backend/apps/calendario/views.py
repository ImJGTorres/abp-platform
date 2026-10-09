import calendar
from datetime import date

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.authentication import UsuarioJWTAuthentication

from .services import detalle_evento, eventos_usuario

MAX_DIAS_RANGO = 92


def _rango(params):
    """(desde, hasta, error). Por defecto, el mes actual."""
    hoy = date.today()
    try:
        desde = date.fromisoformat(params['desde']) if params.get('desde') else hoy.replace(day=1)
        hasta = (date.fromisoformat(params['hasta']) if params.get('hasta')
                 else hoy.replace(day=calendar.monthrange(hoy.year, hoy.month)[1]))
    except ValueError:
        return None, None, 'Las fechas deben tener el formato AAAA-MM-DD.'
    if desde > hasta:
        return None, None, 'La fecha "desde" no puede ser posterior a "hasta".'
    if (hasta - desde).days > MAX_DIAS_RANGO:
        return None, None, f'El rango no puede superar {MAX_DIAS_RANGO} días.'
    return desde, hasta, None


class CalendarioView(APIView):
    """
    GET /api/calendario/?desde=AAAA-MM-DD&hasta=AAAA-MM-DD (HU-040)
    Hitos, entregas, revisiones y fechas límite de actividades de los proyectos del usuario.
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request):
        desde, hasta, error = _rango(request.query_params)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        eventos = eventos_usuario(request.user, desde, hasta)
        return Response({
            'desde': desde.isoformat(),
            'hasta': hasta.isoformat(),
            'total': len(eventos),
            'eventos': eventos,
        })


class CalendarioEventoView(APIView):
    """GET /api/calendario/<evento_id>/ — detalle de 'hito-<id>' o 'actividad-<id>' (HU-040)."""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, evento_id):
        detalle = detalle_evento(request.user, evento_id)
        if detalle is None:
            return Response({'detail': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(detalle)
