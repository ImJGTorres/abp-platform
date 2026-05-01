from django.urls import path

from apps.equipos.views import EstudiantesDisponiblesView
from .views import (
    CursoCargaMasivaView,
    CursoDetailView,
    CursoListCreateView,
    DocenteListView,
    ProyectoListCreateView,
)

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('carga-masiva/', CursoCargaMasivaView.as_view(), name='curso-carga-masiva'),
    path('docentes/', DocenteListView.as_view(), name='docente-list'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    path('<int:curso_id>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
    path('<int:curso_id>/estudiantes/', EstudiantesDisponiblesView.as_view(), name='estudiantes-disponibles'),
]
