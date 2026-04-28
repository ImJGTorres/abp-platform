from django.urls import path

from apps.equipos.views import EstudiantesDisponiblesView
from .views import CursoDetailView, CursoListCreateView, ProyectoListCreateView

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    # GET/POST /api/cursos/<curso_id>/proyectos/
    path('<int:curso_id>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
    path('<int:curso_id>/estudiantes/', EstudiantesDisponiblesView.as_view(), name='estudiantes-disponibles'),
]