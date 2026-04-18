from django.urls import path
from apps.bitacora.views import BitacoraListView

# Rutas del módulo de bitácora
urlpatterns = [
    # Endpoint para listar los registros de bitácora (GET /api/bitacora/)
    path('', BitacoraListView.as_view(), name='bitacora-list'),
]