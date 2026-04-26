from django.urls import path
<<<<<<< HEAD

from .views import ProyectoEquiposView, EquipoUpdateView

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', ProyectoEquiposView.as_view(), name='proyecto-equipos'),
    path('equipos/<int:equipo_id>/', EquipoUpdateView.as_view(), name='equipo-update'),
]
=======
from .views import EquiposPorProyectoView, EstudiantesEquipoView, AsignarEstudiantesView

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', EquiposPorProyectoView.as_view(),  name='equipos-por-proyecto'),
    path('equipos/<int:equipo_id>/estudiantes/', EstudiantesEquipoView.as_view(),   name='estudiantes-equipo'),
    path('equipos/<int:equipo_id>/asignar/',     AsignarEstudiantesView.as_view(),  name='asignar-estudiantes'),
]
>>>>>>> develop
