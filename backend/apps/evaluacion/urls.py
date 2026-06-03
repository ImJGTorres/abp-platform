from django.urls import path

from .views import (
    AutoevaluacionListCreateView,
    AutoevaluacionMiaView,
    AutoevaluacionPuedeView,
    CoevaluacionListCreateView,
    EvaluacionListCreateView,
    EvaluacionPublicarView,
    ProyectoRubricaListCreateView,
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
    path(
        'proyectos/<int:proyecto_id>/rubricas/',
        ProyectoRubricaListCreateView.as_view(),
        name='proyecto-rubrica-list-create',
    ),

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

    # HU-26 — Autoevaluación
    # IMPORTANTE: rutas más específicas primero para no colisionar
    path(
        'proyectos/<int:proyecto_id>/autoevaluaciones/mia/',
        AutoevaluacionMiaView.as_view(),
        name='autoevaluacion-mia',
    ),
    path(
        'proyectos/<int:id_proyecto>/puede-autoevaluar/',
        AutoevaluacionPuedeView.as_view(),
        name='autoevaluacion-puede',
    ),
    path(
        'proyectos/<int:id_proyecto>/autoevaluaciones/',
        AutoevaluacionListCreateView.as_view(),
        name='autoevaluacion-list-create',
    ),

    # HU-27 — Coevaluación
    path(
        'proyectos/<int:id_proyecto>/coevaluaciones/',
        CoevaluacionListCreateView.as_view(),
        name='coevaluacion-list-create',
    ),
]