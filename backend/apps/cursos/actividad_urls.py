from django.urls import path

from .views import ActividadDetailView

urlpatterns = [
    # GET    /api/actividades/<pk>/ — detalle.
    # PUT    /api/actividades/<pk>/ — actualizar todos los campos.
    # PATCH  /api/actividades/<pk>/ — actualización parcial.
    # DELETE /api/actividades/<pk>/ — eliminar (409 si hay dependencias).
    path('<int:pk>/', ActividadDetailView.as_view(), name='actividad-detail'),
]
