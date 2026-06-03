from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from apps.usuarios.authentication import UsuarioJWTAuthentication
from .models import Alerta
from .serializers import AlertaSerializer


class AlertaListView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request):
        usuario_id = request.user.id

        estado = request.query_params.get('estado', 'no_leida')
        estados_validos = ['no_leida', 'leida', 'descartada', 'todas']
        if estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Alerta.objects.filter(id_usuario_destino_id=usuario_id)
        if estado != 'todas':
            qs = qs.filter(estado=estado)

        total_no_leidas = Alerta.objects.filter(
            id_usuario_destino_id=usuario_id,
            estado='no_leida',
        ).count()

        serializer = AlertaSerializer(qs, many=True)
        return Response({
            'total_no_leidas': total_no_leidas,
            'total': qs.count(),
            'alertas': serializer.data,
        }, status=status.HTTP_200_OK)


class AlertaMarcarLeidaView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def patch(self, request, alerta_id):
        usuario_id = request.user.id

        try:
            alerta = Alerta.objects.get(id=alerta_id, id_usuario_destino_id=usuario_id)
        except Alerta.DoesNotExist:
            return Response({'error': 'Alerta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if alerta.estado == 'leida':
            return Response(AlertaSerializer(alerta).data, status=status.HTTP_200_OK)

        alerta.estado = 'leida'
        alerta.fecha_lectura = timezone.now()
        alerta.save(update_fields=['estado', 'fecha_lectura'])

        return Response(AlertaSerializer(alerta).data, status=status.HTTP_200_OK)
