from django.urls import path
from apps.cursos.views import ActividadesPorEquipoView
from .views import (
    ActualizarRolView,
    AsignarEstudiantesView,
    EquiposPorProyectoView,
    EditarEquipoView,
    EstudiantesEquipoView,
    RetirarMiembroView,
    MoverMiembroView,
    DisolverEquipoView,
    ActualizarRolMiembroView,
)

"""
HU-013 — Gestión de equipos y membresías
Endpoints implementados:

Editar equipo — PUT /api/equipos/<equipo_id>/
Reubicar estudiante — POST /api/equipos/<equipo_id>/miembros/mover/
Disolver equipo — DELETE /api/equipos/<equipo_id>/disolver/
Registro de cambios en bitácora para todas las operaciones CRUD
Historial de cambios en membresías preservado mediante soft-delete
"""

urlpatterns = [
    # GET/POST — Listar y crear equipos de un proyecto
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(), name='equipos-por-proyecto'),
    # GET — Obtener estudiantes del equipo (activos, en otros equipos, disponibles)
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(), name='estudiantes-equipo'),
    # POST — Asignación masiva de estudiantes al equipo
    path('equipos/<int:equipo_id>/asignar/', AsignarEstudiantesView.as_view(), name='asignar-estudiantes'),
    # DELETE — Retirar estudiante del equipo (soft-delete)
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/', RetirarMiembroView.as_view(), name='miembro-retirar'),
    # PATCH — Actualizar rol interno de un miembro
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/rol/', ActualizarRolView.as_view(), name='miembro-rol'),
    # PUT/PATCH — Editar nombre, descripción y cupo máximo del equipo
    path('equipos/<int:equipo_id>/', EditarEquipoView.as_view(), name='equipo-editar'),
    # POST — Reubicar un estudiante de este equipo a otro del mismo proyecto
    path('equipos/<int:equipo_id>/miembros/mover/', MoverMiembroView.as_view(), name='miembro-mover'),
    # DELETE — Disolver equipo (soft-delete)
    path('equipos/<int:equipo_id>/disolver/', DisolverEquipoView.as_view(), name='equipo-disolver'),
    # PATCH /api/miembros/<miembro_id>/
    # Actualizar rol_interno de un miembro (lider, desarrollador, analista, disenador, tester, "").
    path('miembros/<int:miembro_id>/', ActualizarRolMiembroView.as_view(), name='miembro-actualizar-rol'),
    # GET /api/equipos/<equipo_id>/actividades/ — lista actividades del equipo (HU-016 BE-03).
    path('equipos/<int:equipo_id>/actividades/', ActividadesPorEquipoView.as_view(), name='actividades-por-equipo'),
]
