from django.urls import path

from .views import (
    FaseListCreateView,
    HitoListCreateView,
    ObjetivoListCreateView,
    ProyectoDashboardView,
    ProyectoDetailView,
    ProyectoEquiposResumenView,
    ProyectoProgresoView,
    RapListCreateView,
)

urlpatterns = [
    # GET/PUT/PATCH  /api/proyectos/<pk>/
    path('<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),

    # GET  /api/proyectos/<proyecto_id>/objetivos/
    # POST /api/proyectos/<proyecto_id>/objetivos/
    path('<int:proyecto_id>/objetivos/', ObjetivoListCreateView.as_view(), name='objetivo-list-create'),

    # GET  /api/proyectos/<proyecto_id>/hitos/
    # POST /api/proyectos/<proyecto_id>/hitos/
    path('<int:proyecto_id>/hitos/', HitoListCreateView.as_view(), name='hito-list-create'),

    # GET  /api/proyectos/<id_proyecto>/raps/
    # POST /api/proyectos/<id_proyecto>/raps/
    path('<int:id_proyecto>/raps/', RapListCreateView.as_view(), name='rap-list-create'),

    # GET  /api/proyectos/<proyecto_id>/fases/  — lista fases del proyecto ordenadas por orden.
    # POST /api/proyectos/<proyecto_id>/fases/  — crea una fase (solo docente propietario).
    path('<int:proyecto_id>/fases/', FaseListCreateView.as_view(), name='fase-list-create'),

    # GET  /api/proyectos/<pk>/progreso/  — resumen de progreso del proyecto (BE 01 HU-27).
    path('<int:pk>/progreso/', ProyectoProgresoView.as_view(), name='proyecto-progreso'),

    # GET  /api/proyectos/<proyecto_id>/dashboard/  — dashboard ejecutivo (HU-28 BE-01).
    path('<int:proyecto_id>/dashboard/', ProyectoDashboardView.as_view(), name='proyecto-dashboard'),

    # GET  /api/proyectos/<proyecto_id>/equipos-resumen/  — resumen por equipo (HU-28 BE-02).
    path('<int:proyecto_id>/equipos-resumen/', ProyectoEquiposResumenView.as_view(), name='proyecto-equipos-resumen'),
]
