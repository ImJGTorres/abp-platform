from django.urls import path

from .views import BajoRendimientoView, RendimientoEstudianteView

urlpatterns = [
    path('bajo-rendimiento/', BajoRendimientoView.as_view(), name='reporte-bajo-rendimiento'),
    path('estudiantes/<int:estudiante_id>/rendimiento/', RendimientoEstudianteView.as_view(), name='rendimiento-estudiante'),
]
