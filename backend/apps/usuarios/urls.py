from django.urls import path
from apps.usuarios.views import (
    CargaMasivaDocentesView,
    CargaMasivaEstudiantesView,
    SubirFotoPerfilView,
    UsuarioCreateView,
    UsuarioProfileView,
    UsuarioUpdateView,
)

urlpatterns = [
    path('', UsuarioCreateView.as_view(), name='usuario-create'),
    path('carga-masiva/', CargaMasivaEstudiantesView.as_view(), name='carga-masiva-estudiantes'),
    path('docentes/carga-masiva/', CargaMasivaDocentesView.as_view(), name='carga-masiva-docentes'),
    path('foto-perfil/', SubirFotoPerfilView.as_view(), name='subir-foto-perfil'),
    path('perfil/', UsuarioProfileView.as_view(), name='usuario-perfil'),
    path('<int:pk>/', UsuarioUpdateView.as_view(), name='usuario-update'),
]