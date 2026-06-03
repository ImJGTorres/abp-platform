"""
HU-013 — Gestión de equipos y membresías.

Este módulo define las rutas URL para la gestión completa de equipos dentro
de un proyecto. Incluye operaciones de creación, edición, disolución,
asignación y reubicación de miembros.

Endpoints implementados:
    - Listar / crear equipos de un proyecto.
    - Editar equipo (nombre, descripción, cupo máximo).
    - Reubicar estudiante entre equipos del mismo proyecto.
    - Disolver equipo (soft-delete con retiro de todos sus miembros).
    - Todas las operaciones CRUD registran eventos en BitacoraSistema.
    - El historial de membresías se preserva mediante soft-delete.
"""

from django.urls import path
from apps.cursos.views import ActividadesPorEquipoView
from .views import (
    ActualizarRolView,
    AsignarEstudiantesView,
    DisolverEquipoView,
    EditarEquipoView,
    EquipoProgresoView,
    EquiposPorProyectoView,
    EstudiantesEquipoView,
    MisEquiposView,
    MoverMiembroView,
    RetirarMiembroView,
    ActualizarRolMiembroView,
)

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

    # GET /api/equipos/<equipo_id>/progreso/ — resumen de progreso del equipo (BE 02).
    path('equipos/<int:equipo_id>/progreso/', EquipoProgresoView.as_view(), name='equipo-progreso'),
    # GET /api/mis-equipos/ — equipos y actividades del estudiante autenticado.
    path('mis-equipos/', MisEquiposView.as_view(), name='mis-equipos'),
]
