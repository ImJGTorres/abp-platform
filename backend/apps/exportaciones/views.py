import os
from django.http import FileResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.usuarios.authentication import UsuarioJWTAuthentication
from .models import Exportacion
from .services import generar_exportacion

TIPOS_VALIDOS = {'proyecto', 'estudiante', 'equipo', 'indicadores', 'tendencia'}
FORMATOS_VALIDOS = {'pdf', 'excel'}
PARAMS_REQUERIDOS = {
    'proyecto': ['proyecto_id'],
    'estudiante': ['estudiante_id', 'proyecto_id'],
    'equipo': ['equipo_id'],
    'indicadores': [],
    'tendencia': [],
}


class SolicitarExportacionView(APIView):
    """POST /api/exportar/reporte/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def post(self, request):
        usuario = request.user
        data = request.data

        tipo = data.get('tipo_reporte')
        formato = data.get('formato')
        parametros = data.get('parametros', {})

        if tipo not in TIPOS_VALIDOS:
            return Response(
                {'error': f'tipo_reporte inválido. Opciones: {list(TIPOS_VALIDOS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if formato not in FORMATOS_VALIDOS:
            return Response(
                {'error': f'formato inválido. Opciones: {list(FORMATOS_VALIDOS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requeridos = PARAMS_REQUERIDOS[tipo]
        faltantes = [p for p in requeridos if p not in parametros]
        if faltantes:
            return Response(
                {'error': f'Parámetros requeridos para {tipo}: {faltantes}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exp = Exportacion.objects.create(
            id_usuario=usuario,
            tipo_reporte=tipo,
            formato=formato,
            parametros=parametros,
            estado='generando',
        )

        generar_exportacion(exp.id)
        exp.refresh_from_db()

        return Response({
            'id': exp.id,
            'estado': exp.estado,
            'mensaje_error': exp.mensaje_error,
        }, status=status.HTTP_201_CREATED)


class EstadoExportacionView(APIView):
    """GET /api/exportar/<exportacion_id>/estado/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, exportacion_id):
        usuario = request.user

        try:
            exp = Exportacion.objects.get(id=exportacion_id, id_usuario=usuario)
        except Exportacion.DoesNotExist:
            return Response({'error': 'Exportación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        respuesta = {
            'id': exp.id,
            'tipo_reporte': exp.tipo_reporte,
            'formato': exp.formato,
            'estado': exp.estado,
            'fecha_solicitud': exp.fecha_solicitud.isoformat(),
            'fecha_disponible': exp.fecha_disponible.isoformat() if exp.fecha_disponible else None,
            'mensaje_error': exp.mensaje_error,
            'url_descarga': None,
        }

        if exp.estado == 'listo' and exp.ruta_archivo:
            rel = os.path.relpath(exp.ruta_archivo, settings.MEDIA_ROOT)
            respuesta['url_descarga'] = f"{settings.MEDIA_URL}{rel}"

        return Response(respuesta, status=status.HTTP_200_OK)


class DescargarExportacionView(APIView):
    """GET /api/exportar/<exportacion_id>/descargar/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def get(self, request, exportacion_id):
        usuario = request.user

        try:
            exp = Exportacion.objects.get(id=exportacion_id, id_usuario=usuario)
        except Exportacion.DoesNotExist:
            return Response({'error': 'No encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if exp.estado != 'listo' or not exp.ruta_archivo:
            return Response({'error': 'Archivo no disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        if not os.path.exists(exp.ruta_archivo):
            return Response({'error': 'Archivo no encontrado en disco.'}, status=status.HTTP_404_NOT_FOUND)

        ext = 'pdf' if exp.formato == 'pdf' else 'xlsx'
        content_type = (
            'application/pdf' if exp.formato == 'pdf'
            else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        nombre_descarga = f"reporte_{exp.tipo_reporte}_{exp.id}.{ext}"

        return FileResponse(
            open(exp.ruta_archivo, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=nombre_descarga,
        )
