from django.urls import path

from .views import (
    ActividadAsignarResponsableView,
    ActividadAsignarView,
    ActividadDetailView,
    AvanceActividadListCreateView,
)

urlpatterns = [
    # GET    /api/actividades/<pk>/ — detalle.
    # PUT    /api/actividades/<pk>/ — actualizar todos los campos.
    # PATCH  /api/actividades/<pk>/ — actualización parcial.
    # DELETE /api/actividades/<pk>/ — eliminar (409 si hay dependencias).
    path('<int:pk>/', ActividadDetailView.as_view(), name='actividad-detail'),
    # PATCH  /api/actividades/<pk>/asignar-responsable/ — líder asigna un responsable (FK).
    path('<int:pk>/asignar-responsable/', ActividadAsignarResponsableView.as_view(), name='actividad-asignar-responsable'),
    # PATCH  /api/actividades/<pk>/asignar/ — líder asigna uno o más responsables (HU-016 BE-02).
    path('<int:pk>/asignar/', ActividadAsignarView.as_view(), name='actividad-asignar'),
    # GET  /api/actividades/<actividad_id>/avances/ — lista avances.
    # POST /api/actividades/<actividad_id>/avances/ — registra avance.
    path('<int:actividad_id>/avances/', AvanceActividadListCreateView.as_view(), name='avance-list-create'),
]
