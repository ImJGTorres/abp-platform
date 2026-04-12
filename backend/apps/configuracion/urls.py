from django.urls import path
# path: Función de Django para definir rutas URL simples

from .views import ConfiguracionView
# ConfiguracionView: Vista que maneja las solicitudes GET y PATCH de configuración


# =============================================================================
# URLS DEL MÓDULO DE CONFIGURACIÓN
# =============================================================================

urlpatterns = [
    # Ruta principal: GET /api/configuracion/
    # Retorna todos los parámetros agrupados por categoría
    # Requiere rol de administrador
    path('', ConfiguracionView.as_view(), name='configuracion'),
    
    # Ruta con parámetro: PATCH /api/configuracion/<clave>/
    # Permite actualizar un parámetro específico por su clave
    # Ejemplo: PATCH /api/configuracion/max_estudiantes_por_equipo/
    # Requiere rol de administrador
    path('<str:clave>/', ConfiguracionView.as_view(), name='configuracion_clave'),
]