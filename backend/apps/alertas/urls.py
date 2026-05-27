from django.urls import path
from .views import AlertaListView, AlertaMarcarLeidaView

urlpatterns = [
    path('', AlertaListView.as_view(), name='alertas-list'),
    path('<int:alerta_id>/leer/', AlertaMarcarLeidaView.as_view(), name='alerta-marcar-leida'),
]
