from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.serializers import BitacoraSerializer


class BitacoraPagination(PageNumberPagination):
    """Configuración de paginación para el endpoint de bitácora."""
    page_size = 50


class BitacoraListView(APIView):
    """Vista para listar los registros de bitácora del sistema."""
    # Solo administradores pueden acceder a esta vista
    permission_classes = [IsAdminUser]
    # Restringe los métodos HTTP permitidos a solo lectura
    http_method_names = ['get', 'head', 'options']
    
    def get(self, request):
        # Obtiene todos los registros ordenados por fecha descendente
        queryset = BitacoraSistema.objects.all().order_by('-fecha_hora')
        
        # Filtro por ID de usuario
        usuario_id = request.query_params.get('usuario')
        if usuario_id:
            queryset = queryset.filter(id_usuario_id=usuario_id)
        
        # Filtro por nombre del módulo
        modulo = request.query_params.get('modulo')
        if modulo:
            queryset = queryset.filter(modulo=modulo)
        
        # Filtro por tipo de acción
        accion = request.query_params.get('accion')
        if accion:
            queryset = queryset.filter(accion=accion)
        
        # Filtro por fecha de inicio
        fecha_desde = request.query_params.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_hora__date__gte=fecha_desde)
        
        # Filtro por fecha de fin
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora__date__lte=fecha_hasta)
        
        # Aplica paginación y retorna los resultados
        paginator = BitacoraPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BitacoraSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = BitacoraSerializer(queryset, many=True)
        return Response(serializer.data)