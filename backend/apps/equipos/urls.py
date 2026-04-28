from django.urls import path
from .views import (
    ActualizarRolView,
    AsignarEstudiantesView,
    EquiposPorProyectoView,
    EquipoUpdateView,
    EstudiantesEquipoView,
    MiembroListView,
    RetirarMiembroView,
    EditarEquipoView,
    MoverMiembroView,
    DisolverEquipoView,
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
    # PUT/PATCH /api/equipos/<equipo_id>/  — editar nombre, descripción y cupo del equipo.
    path('equipos/<int:equipo_id>/', EditarEquipoView.as_view(), name='equipo-editar'),
    # POST /api/equipos/<equipo_id>/miembros/mover/  — reubicar estudiante a otro equipo del mismo proyecto.
    path('equipos/<int:equipo_id>/miembros/mover/', MoverMiembroView.as_view(), name='miembro-mover'),
    # DELETE /api/equipos/<equipo_id>/disolver/  — disolver equipo (soft-delete).
    path('equipos/<int:equipo_id>/disolver/', DisolverEquipoView.as_view(), name='equipo-disolver'),
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(),  name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/',             EquipoUpdateView.as_view(),         name='equipo-update'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(),    name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/',     AsignarEstudiantesView.as_view(),   name='asignar-estudiantes'),
    path('equipos/<int:equipo_id>/miembros/',    MiembroListView.as_view(),          name='miembro-list'),
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/',       RetirarMiembroView.as_view(),  name='miembro-retirar'),
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/rol/',   ActualizarRolView.as_view(),   name='miembro-rol'),
]
