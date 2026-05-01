from django.urls import path

from .views import ObjetivoListCreateView, ProyectoDetailView, RapListCreateView

urlpatterns = [
    # GET/PUT/PATCH  /api/proyectos/<pk>/
    # Detalle, edición parcial y actualización completa de un proyecto.
    path('<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),

    # GET  /api/proyectos/<proyecto_id>/objetivos/  — lista objetivos del proyecto.
    # POST /api/proyectos/<proyecto_id>/objetivos/  — crea uno o varios objetivos.
    # La creación en lote se activa automáticamente cuando el body es un array JSON.
    path('<int:proyecto_id>/objetivos/', ObjetivoListCreateView.as_view(), name='objetivo-list-create'),

    # GET  /api/proyectos/<id_proyecto>/raps/  — lista RAPs del proyecto.
    # POST /api/proyectos/<id_proyecto>/raps/  — crea un RAP asociado al proyecto.
    path('<int:id_proyecto>/raps/', RapListCreateView.as_view(), name='rap-list-create'),
]
