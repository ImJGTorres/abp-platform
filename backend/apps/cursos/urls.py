from django.urls import path

from .views import CursoDetailView, CursoListCreateView
from apps.equipos.views import EstudiantesDisponiblesView

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
    # Listar estudiantes del curso que no han sido asignados a un equipo del proyecto.
    path('<int:curso_id>/estudiantes/', EstudiantesDisponiblesView.as_view(), name='estudiantes-disponibles'),
]