from django.urls import path

from .views import ObjetivoDetailView

urlpatterns = [
    # GET    /api/objetivos/<pk>/  — detalle del objetivo.
    # PUT    /api/objetivos/<pk>/  — actualiza descripcion, tipo y orden.
    # PATCH  /api/objetivos/<pk>/  — actualización parcial.
    # DELETE /api/objetivos/<pk>/  — elimina y reordena los restantes.
    path('<int:pk>/', ObjetivoDetailView.as_view(), name='objetivo-detail'),
]