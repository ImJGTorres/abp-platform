from django.urls import path

from .views import ActividadAsignarResponsableView, ActividadDetailView

urlpatterns = [
    # GET    /api/actividades/<pk>/ — detalle.
    # PUT    /api/actividades/<pk>/ — actualizar todos los campos.
    # PATCH  /api/actividades/<pk>/ — actualización parcial.
    # DELETE /api/actividades/<pk>/ — eliminar (409 si hay dependencias).
    path('<int:pk>/', ActividadDetailView.as_view(), name='actividad-detail'),
    # PATCH  /api/actividades/<pk>/asignar-responsable/ — líder asigna responsable.
    path('<int:pk>/asignar-responsable/', ActividadAsignarResponsableView.as_view(), name='actividad-asignar-responsable'),
]
