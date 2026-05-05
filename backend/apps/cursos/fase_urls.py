from django.urls import path

from .views import ActividadListCreateView

urlpatterns = [
    # GET  /api/fases/<fase_id>/actividades/ — lista actividades de la fase.
    # POST /api/fases/<fase_id>/actividades/ — crea actividad (docente propietario).
    path('<int:fase_id>/actividades/', ActividadListCreateView.as_view(), name='actividad-list-create'),
]