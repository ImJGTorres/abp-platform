from django.urls import path

from .views import BajoRendimientoView, RendimientoEstudianteView, ReporteCursoView, ReporteProyectoView

urlpatterns = [
    path('bajo-rendimiento/', BajoRendimientoView.as_view(), name='reporte-bajo-rendimiento'),
    path('estudiantes/<int:estudiante_id>/rendimiento/', RendimientoEstudianteView.as_view(), name='rendimiento-estudiante'),
    path('proyecto/<int:proyecto_id>/', ReporteProyectoView.as_view(), name='reporte-proyecto'),
    path('curso/<int:curso_id>/', ReporteCursoView.as_view(), name='reporte-curso'),
]
