from django.urls import path
from . import views

urlpatterns = [
    path(
        'actividades/<int:id_actividad>/entregables/',
        views.EntregableListCreateView.as_view(),
        name='entregable-list-create',
    ),
    path(
        'entregables/<int:pk>/enviar/',
        views.EnviarEntregableView.as_view(),
        name='entregable-enviar',
    ),
    path(
        'entregables/<int:id_entregable>/archivos/',
        views.ArchivoListCreateView.as_view(),
        name='archivo-list-create',
    ),
    path(
        'archivos/<int:archivo_id>/',
        views.ArchivoAdjuntoEliminarView.as_view(),
        name='archivo-eliminar',
    ),
    # HU-021 — Versionado de entregables
    path(
        'entregables/<int:pk>/nueva-version/',
        views.NuevaVersionEntregableView.as_view(),
        name='entregable-nueva-version',
    ),
    path(
        'entregables/<int:pk>/versiones/',
        views.HistorialVersionesView.as_view(),
        name='entregable-versiones',
    ),
    # HU-022 — Validación de entregables
    path(
        'entregables/<int:entregable_id>/aprobar/',
        views.EntregableAprobarView.as_view(),
        name='entregable-aprobar',
    ),
    path(
        'entregables/<int:entregable_id>/rechazar/',
        views.EntregableRechazarView.as_view(),
        name='entregable-rechazar',
    ),
    path(
        'proyectos/<int:proyecto_id>/entregables-pendientes/',
        views.EntregablesPendientesView.as_view(),
        name='entregables-pendientes',
    ),
]
