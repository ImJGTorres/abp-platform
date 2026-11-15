import os
from datetime import timedelta

from django.http import FileResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.reportes.acceso import puede_ver_reporte
from apps.usuarios.authentication import UsuarioJWTAuthentication
from .models import Exportacion
from .services import generar_exportacion

MAX_EXPORTACIONES_POR_HORA = 30
TIPOS_VALIDOS = {'proyecto', 'estudiante', 'equipo', 'indicadores', 'tendencia'}
FORMATOS_VALIDOS = {'pdf', 'excel'}
PARAMS_REQUERIDOS = {
    'proyecto': ['proyecto_id'],
    'estudiante': ['estudiante_id', 'proyecto_id'],
    'equipo': ['equipo_id'],
    'indicadores': [],
    'tendencia': [],
}


def _excede_limite(usuario):
    """Las exportaciones se generan dentro de la petición: se acota cuántas puede pedir un usuario."""
    reciente = timezone.now() - timedelta(hours=1)
    return Exportacion.objects.filter(
        id_usuario=usuario, fecha_solicitud__gte=reciente
    ).count() >= MAX_EXPORTACIONES_POR_HORA


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

        if not isinstance(parametros, dict):
            return Response({'error': 'parametros debe ser un objeto.'}, status=status.HTTP_400_BAD_REQUEST)

        requeridos = PARAMS_REQUERIDOS[tipo]
        faltantes = [p for p in requeridos if p not in parametros]
        if faltantes:
            return Response(
                {'error': f'Parámetros requeridos para {tipo}: {faltantes}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Los ids y n_periodos deben ser enteros; n_periodos se acota para no
        # generar reportes arbitrariamente grandes dentro de la petición.
        for clave in ('proyecto_id', 'estudiante_id', 'equipo_id', 'periodo_id', 'curso_id', 'n_periodos'):
            if parametros.get(clave) is not None:
                try:
                    parametros[clave] = int(parametros[clave])
                except (TypeError, ValueError):
                    return Response({'error': f'{clave} debe ser un entero.'}, status=status.HTTP_400_BAD_REQUEST)
        if 'n_periodos' in parametros:
            parametros['n_periodos'] = max(2, min(parametros['n_periodos'], 10))

        # Mismas reglas de acceso que la API de reportes
        if not puede_ver_reporte(usuario, tipo, parametros):
            return Response({'error': 'Sin permiso.'}, status=status.HTTP_403_FORBIDDEN)

        if _excede_limite(usuario):
            return Response(
                {'error': 'Superaste el límite de exportaciones por hora. Intenta más tarde.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
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
            # Siempre por la vista autenticada: /media/ no tiene control de acceso
            respuesta['url_descarga'] = f'/api/exportar/{exp.id}/descargar/'

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
