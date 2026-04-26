from django.urls import path
from .views import (
    EquiposPorProyectoView,
    EstudiantesEquipoView,
    AsignarEstudiantesView,
    MiembroListView,
    RetirarMiembroView,
)

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(), name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(), name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/', AsignarEstudiantesView.as_view(), name='asignar-estudiantes'),
    # BE-03: GET  /api/equipos/<equipo_id>/miembros/
    # POST a este mismo path también está manejado por MiembroListView
    path('equipos/<int:equipo_id>/miembros/', MiembroListView.as_view(), name='miembro-list'),
    # BE-04: DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/', RetirarMiembroView.as_view(), name='miembro-retirar'),
]
