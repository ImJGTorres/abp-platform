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
]
