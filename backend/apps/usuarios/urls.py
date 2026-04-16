from django.urls import path
from apps.usuarios.views import UsuarioCreateView, UsuarioProfileView

urlpatterns = [
    path('', UsuarioCreateView.as_view(), name='usuario-create'),
    path('perfil/', UsuarioProfileView.as_view(), name='usuario-perfil'),
]