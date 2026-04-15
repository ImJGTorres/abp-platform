from django.urls import path, include
# path: Función de Django para definir rutas URL simples
# include: Función para incluir URLs de otras aplicaciones

from rest_framework.routers import DefaultRouter
# DefaultRouter: Router de DRF que genera automáticamente rutas para ViewSets

from .views import ConfiguracionView, PeriodoAcademicoViewSet
# ConfiguracionView: Vista que maneja las solicitudes GET y PATCH de configuración
# PeriodoAcademicoViewSet: ViewSet para períodos académicos


# =============================================================================
# ROUTER PARA VIEWSETS
# =============================================================================

router = DefaultRouter()
router.register(r'periodos', PeriodoAcademicoViewSet, basename='periodos')


# =============================================================================
# URLS DEL MÓDULO DE CONFIGURACIÓN
# =============================================================================

urlpatterns = [
    # Rutas del router para ViewSets (periodos académicos)
    path('', include(router.urls)),
    
    # Ruta principal: GET /api/configuracion/
    # Retorna todos los parámetros agrupados por categoría
    # Requiere rol de administrador
    path('configuracion/', ConfiguracionView.as_view(), name='configuracion'),

    # Ruta con parámetro: PATCH /api/configuracion/<clave>/
    # Permite actualizar un parámetro específico por su clave
    # Ejemplo: PATCH /api/configuracion/max_estudiantes_por_equipo/
    # Requiere rol de administrador
    path('configuracion/<str:clave>/', ConfiguracionView.as_view(), name='configuracion_clave'),
]