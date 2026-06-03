from django.urls import path
from .views import SolicitarExportacionView, EstadoExportacionView, DescargarExportacionView

urlpatterns = [
    path('reporte/', SolicitarExportacionView.as_view(), name='exportar-solicitar'),
    path('<int:exportacion_id>/estado/', EstadoExportacionView.as_view(), name='exportar-estado'),
    path('<int:exportacion_id>/descargar/', DescargarExportacionView.as_view(), name='exportar-descargar'),
]
