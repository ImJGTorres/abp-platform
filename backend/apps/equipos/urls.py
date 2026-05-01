from django.urls import path
from .views import (
    EquiposPorProyectoView,
    EstudiantesEquipoView,
    AsignarEstudiantesView,
    MiembroListView,
    RetirarMiembroView,
    ActualizarRolMiembroView,
)

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(), name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(), name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/', AsignarEstudiantesView.as_view(), name='asignar-estudiantes'),
    # GET /api/equipos/<equipo_id>/miembros/
    # Listar miembros activos del equipo con su rol interno y fecha de asignación.
    path('equipos/<int:equipo_id>/miembros/', MiembroListView.as_view(), name='miembro-list'),
    # DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/
    # Retirar estudiante del equipo (soft-delete: marca como retirado y libera cupo).
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/', RetirarMiembroView.as_view(), name='miembro-retirar'),
    # PATCH /api/miembros/<miembro_id>/
    # Actualizar rol_interno de un miembro (lider, desarrollador, analista, disenador, tester, "").
    path('miembros/<int:miembro_id>/', ActualizarRolMiembroView.as_view(), name='miembro-actualizar-rol'),
]
