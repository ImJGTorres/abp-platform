from django.urls import path

from .views import ObjetivoListCreateView, ProyectoDetailView

urlpatterns = [
    # GET/PUT/PATCH  /api/proyectos/<pk>/
    # Detalle, edición parcial y actualización completa de un proyecto.
    path('<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),

    # GET  /api/proyectos/<proyecto_id>/objetivos/  — lista objetivos del proyecto.
    # POST /api/proyectos/<proyecto_id>/objetivos/  — crea uno o varios objetivos.
    # La creación en lote se activa automáticamente cuando el body es un array JSON.
    path('<int:proyecto_id>/objetivos/', ObjetivoListCreateView.as_view(), name='objetivo-list-create'),
]