from django.urls import path
from apps.usuarios.views import UsuarioCreateView

urlpatterns = [
    path('', UsuarioCreateView.as_view(), name='usuario-create'),
]