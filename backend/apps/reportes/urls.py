from django.urls import path

from .views import (
    BajoRendimientoView,
    RendimientoEstudianteView,
    ReporteCursoView,
    ReporteProyectoView,
    ReporteEstudianteProyectoView,
    ReporteEquipoEstudiantesView,
)

urlpatterns = [
    path('bajo-rendimiento/', BajoRendimientoView.as_view(), name='reporte-bajo-rendimiento'),
    path('estudiantes/<int:estudiante_id>/rendimiento/', RendimientoEstudianteView.as_view(), name='rendimiento-estudiante'),
    path('proyecto/<int:proyecto_id>/', ReporteProyectoView.as_view(), name='reporte-proyecto'),
    path('curso/<int:curso_id>/', ReporteCursoView.as_view(), name='reporte-curso'),
    path('estudiante/<int:estudiante_id>/proyecto/<int:proyecto_id>/',
         ReporteEstudianteProyectoView.as_view(), name='reporte-estudiante-proyecto'),
    path('equipo/<int:equipo_id>/estudiantes/',
         ReporteEquipoEstudiantesView.as_view(), name='reporte-equipo-estudiantes'),
]
