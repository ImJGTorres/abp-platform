from django.urls import path
from apps.usuarios.views import UsuarioCreateView, UsuarioProfileView, UsuarioUpdateView

urlpatterns = [
    path('', UsuarioCreateView.as_view(), name='usuario-create'),
    path('perfil/', UsuarioProfileView.as_view(), name='usuario-perfil'),
    path('<int:pk>/', UsuarioUpdateView.as_view(), name='usuario-update'),
]