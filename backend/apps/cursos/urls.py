from django.urls import path

from apps.equipos.views import EstudiantesDisponiblesView
from .views import (
    CursoCargaMasivaView,
    CursoDetailView,
    CursoListCreateView,
    DocenteListView,
    HitoDetailView,
    ProyectoListCreateView,
    RapDetailView,
    RapListCreateView,
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

# Exportados para incluirse bajo prefijos distintos en config/urls.py
proyectos_urlpatterns = [
    path('<int:id_proyecto>/raps/', RapListCreateView.as_view(), name='rap-list-create'),
]

raps_urlpatterns = [
    path('<int:id>/', RapDetailView.as_view(), name='rap-detail'),
]

# Exportado para incluirse bajo /api/hitos/ en config/urls.py
hitos_urlpatterns = [
    # GET/PUT/PATCH/DELETE  /api/hitos/<pk>/
    path('<int:pk>/', HitoDetailView.as_view(), name='hito-detail'),
]
