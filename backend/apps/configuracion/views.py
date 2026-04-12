from collections import defaultdict

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento

from .cache import get_parametros_cacheados, set_parametros_cacheados, invalidar_cache_parametros
from .models import ParametroSistema
from .permissions import EsAdministrador
from .serializers import ParametroSistemaSerializer


class ConfiguracionView(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        cached_data = get_parametros_cacheados()
        if cached_data is not None:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='configuracion',
                descripcion='Consulta de parámetros del sistema (desde caché)',
            )
            return Response(cached_data)

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

        result = dict(agrupados)
        set_parametros_cacheados(result)

        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='configuracion',
            descripcion='Consulta de parámetros del sistema',
        )
        return Response(result)

    def patch(self, request, clave):
        try:
            parametro = ParametroSistema.objects.get(clave=clave)
        except ParametroSistema.DoesNotExist:
            return Response(
                {'detail': f'Parámetro "{clave}" no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        nuevo_valor = request.data.get('valor')
        if nuevo_valor is None:
            return Response(
                {'detail': 'El campo "valor" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        rango = request.data.get('rango')
        if parametro.tipo_dato == ParametroSistema.TipoDato.INTEGER and rango:
            try:
                valor_int = int(nuevo_valor)
            except ValueError:
                return Response(
                    {'detail': f'Valor debe ser entero, recibido: "{nuevo_valor}"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if 'min' in rango and valor_int < rango['min']:
                return Response(
                    {'detail': f'Valor mínimo permitido: {rango["min"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'max' in rango and valor_int > rango['max']:
                return Response(
                    {'detail': f'Valor máximo permitido: {rango["max"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        parametro.valor = str(nuevo_valor)
        parametro.usuario_modifico = request.user
        try:
            parametro.full_clean()
            parametro.save()
            invalidar_cache_parametros()
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        serializer = ParametroSistemaSerializer(parametro)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='configuracion',
            descripcion=f'Actualización de parámetro "{clave}"',
        )
        return Response(serializer.data)
