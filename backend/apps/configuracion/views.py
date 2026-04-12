from collections import defaultdict

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento

from .models import ParametroSistema
from .permissions import EsAdministrador
from .serializers import ParametroSistemaSerializer


class ConfiguracionView(APIView):
    """
    GET /api/configuracion/

    Retorna todos los parámetros del sistema agrupados por categoría.
    Solo accesible para administradores.
    """
    permission_classes = [EsAdministrador]

    def get(self, request):
        parametros = ParametroSistema.objects.all()
        serializer = ParametroSistemaSerializer(parametros, many=True)

        agrupados = defaultdict(list)
        for item in serializer.data:
            agrupados[item['categoria']].append({
                'clave':              item['clave'],
                'valor':              item['valor'],
                'valor_casteado':     item['valor_casteado'],
                'descripcion':        item['descripcion'],
                'tipo_dato':          item['tipo_dato'],
                'fecha_actualizacion': item['fecha_actualizacion'],
            })

        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='configuracion',
            descripcion='Consulta de parámetros del sistema',
        )
        return Response(dict(agrupados))
