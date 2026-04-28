from django.urls import path

<<<<<<< HEAD
from .views import (
    CursoCargaMasivaView,
    CursoDetailView,
    CursoListCreateView,
    DocenteListView,
    ProyectoDetailView,
    ProyectoListCreateView,
)

from apps.equipos.views import EstudiantesDisponiblesView
=======
from .views import CursoDetailView, CursoListCreateView, ProyectoListCreateView, ProyectoRetrieveUpdateDestroyView
from apps.equipos.views import EstudiantesCursoView
>>>>>>> feature/HU-011-frontend

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('carga-masiva/', CursoCargaMasivaView.as_view(), name='curso-carga-masiva'),
    path('docentes/', DocenteListView.as_view(), name='docente-list'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
<<<<<<< HEAD

    path('<int:curso_pk>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    path('<int:curso_pk>/proyectos/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),

    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
    # Listar estudiantes del curso que no han sido asignados a un equipo del proyecto.
    path('<int:curso_id>/estudiantes/', EstudiantesDisponiblesView.as_view(), name='estudiantes-disponibles'),
=======
    # GET /api/cursos/<curso_id>/estudiantes/           — todos los estudiantes con estado en el curso
    # GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int> — solo disponibles para ese proyecto
    path('<int:curso_id>/estudiantes/', EstudiantesCursoView.as_view(), name='estudiantes-curso'),
    # CRUD de proyectos dentro de un curso
    path('<int:curso_id>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    path('<int:curso_id>/proyectos/<int:pk>/', ProyectoRetrieveUpdateDestroyView.as_view(), name='proyecto-detail'),
>>>>>>> feature/HU-011-frontend
]