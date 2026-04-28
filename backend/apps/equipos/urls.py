from django.urls import path
from .views import (
    ActualizarRolView,
    AsignarEstudiantesView,
    EquiposPorProyectoView,
    EquipoUpdateView,
    EstudiantesEquipoView,
    MiembroListView,
    RetirarMiembroView,
)

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(),  name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/',             EquipoUpdateView.as_view(),         name='equipo-update'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(),    name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/',     AsignarEstudiantesView.as_view(),   name='asignar-estudiantes'),
    path('equipos/<int:equipo_id>/miembros/',    MiembroListView.as_view(),          name='miembro-list'),
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/',       RetirarMiembroView.as_view(),  name='miembro-retirar'),
    path('equipos/<int:equipo_id>/miembros/<int:usuario_id>/rol/',   ActualizarRolView.as_view(),   name='miembro-rol'),
]
