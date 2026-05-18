from django.urls import path

from .views import ActividadListCreateView, FaseDetailView

urlpatterns = [
    # GET/PUT/PATCH  /api/fases/<pk>/       — detalle y edición de la fase.
    # DELETE         /api/fases/<pk>/       — elimina la fase (409 si tiene actividades).
    path('<int:pk>/', FaseDetailView.as_view(), name='fase-detail'),

    # GET  /api/fases/<fase_id>/actividades/ — lista actividades de la fase.
    # POST /api/fases/<fase_id>/actividades/ — crea actividad (docente propietario).
    path('<int:fase_id>/actividades/', ActividadListCreateView.as_view(), name='actividad-list-create'),
]