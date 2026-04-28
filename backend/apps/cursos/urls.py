from django.urls import path

from .views import CursoDetailView, CursoListCreateView, ProyectoListCreateView, ProyectoRetrieveUpdateDestroyView
from apps.equipos.views import EstudiantesCursoView

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    # GET /api/cursos/<curso_id>/estudiantes/           — todos los estudiantes con estado en el curso
    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int> — solo disponibles para ese proyecto
    path('<int:curso_id>/estudiantes/', EstudiantesCursoView.as_view(), name='estudiantes-curso'),
    # CRUD de proyectos dentro de un curso
    path('<int:curso_id>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    path('<int:curso_id>/proyectos/<int:pk>/', ProyectoRetrieveUpdateDestroyView.as_view(), name='proyecto-detail'),
]