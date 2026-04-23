from django.urls import path
from apps.usuarios.views import (
    CargaMasivaEstudiantesView,
    UsuarioCreateView,
    UsuarioProfileView,
    UsuarioUpdateView,
)

urlpatterns = [
    path('', UsuarioCreateView.as_view(), name='usuario-create'),
    path('carga-masiva/', CargaMasivaEstudiantesView.as_view(), name='carga-masiva-estudiantes'),
    path('perfil/', UsuarioProfileView.as_view(), name='usuario-perfil'),
    path('<int:pk>/', UsuarioUpdateView.as_view(), name='usuario-update'),
]