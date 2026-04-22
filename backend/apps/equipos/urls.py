from django.urls import path

from .views import ProyectoEquiposView, EquipoUpdateView

urlpatterns = [
    path('proyectos/<int:proyecto_id>/equipos/', ProyectoEquiposView.as_view(), name='proyecto-equipos'),
    path('equipos/<int:equipo_id>/', EquipoUpdateView.as_view(), name='equipo-update'),
]