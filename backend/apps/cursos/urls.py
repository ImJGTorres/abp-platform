from django.urls import path

from .views import (
    CursoCargaMasivaView,
    CursoDetailView,
    CursoListCreateView,
    DocenteListView,
    ProyectoDetailView,
    ProyectoListCreateView,
)

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('carga-masiva/', CursoCargaMasivaView.as_view(), name='curso-carga-masiva'),
    path('docentes/', DocenteListView.as_view(), name='docente-list'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
    path('<int:curso_pk>/proyectos/', ProyectoListCreateView.as_view(), name='proyecto-list-create'),
    path('<int:curso_pk>/proyectos/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),
]