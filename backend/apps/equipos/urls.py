from django.urls import path
from .views import EquiposPorProyectoView, EstudiantesEquipoView, AsignarEstudiantesView, AsignarEstudianteView

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(),  name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(),   name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/',     AsignarEstudiantesView.as_view(),  name='asignar-estudiantes'),
    path('equipos/<int:id>/miembros/',           AsignarEstudianteView.as_view(),   name='asignar-estudiante'),
]