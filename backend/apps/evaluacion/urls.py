from django.urls import path

from .views import (
    EvaluacionListCreateView,
    EvaluacionPublicarView,
    RetroalimentacionCreateView,
    RetroalimentacionEquipoView,
    RetroalimentacionEstudianteView,
    RubricaDetailView,
    RubricaListCreateView,
)

urlpatterns = [
    # HU-23 — Rúbricas
    path('rubricas/', RubricaListCreateView.as_view(), name='rubrica-list-create'),
    path('rubricas/<int:pk>/', RubricaDetailView.as_view(), name='rubrica-detail'),

    # HU-24 — Evaluaciones de entregables
    path(
        'entregables/<int:id_entregable>/evaluaciones/',
        EvaluacionListCreateView.as_view(),
        name='evaluacion-list-create',
    ),
    path(
        'evaluaciones/<int:pk>/publicar/',
        EvaluacionPublicarView.as_view(),
        name='evaluacion-publicar',
    ),

    # HU-25 — Retroalimentación
    path(
        'proyectos/<int:id_proyecto>/retroalimentaciones/',
        RetroalimentacionCreateView.as_view(),
        name='retroalimentacion-create',
    ),
    path(
        'equipos/<int:id_equipo>/retroalimentaciones/',
        RetroalimentacionEquipoView.as_view(),
        name='retroalimentacion-equipo',
    ),
    path(
        'usuarios/<int:id_usuario>/retroalimentaciones/',
        RetroalimentacionEstudianteView.as_view(),
        name='retroalimentacion-estudiante',
    ),
]