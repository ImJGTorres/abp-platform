from django.urls import path

from .views import CursoDetailView, CursoListCreateView
from apps.equipos.views import EstudiantesDisponiblesView

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    # BE-05: GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
    path('<int:curso_id>/estudiantes/', EstudiantesDisponiblesView.as_view(), name='estudiantes-disponibles'),
]