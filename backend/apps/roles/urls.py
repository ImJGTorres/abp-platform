from django.urls import path

from .views import (
    PermisoDetailView,
    PermisoListCreateView,
    RolDetailView,
    RolListCreateView,
    RolPermisoDetailView,
    RolPermisoListCreateView,
)

urlpatterns = [
    # Roles
    path('', RolListCreateView.as_view(), name='rol-list-create'),
    path('<int:pk>/', RolDetailView.as_view(), name='rol-detail'),

    # Permisos
    path('permisos/', PermisoListCreateView.as_view(), name='permiso-list-create'),
    path('permisos/<int:pk>/', PermisoDetailView.as_view(), name='permiso-detail'),

    # Rol-Permiso
    path('rol-permiso/', RolPermisoListCreateView.as_view(), name='rolpermiso-list-create'),
    path('rol-permiso/<int:pk>/', RolPermisoDetailView.as_view(), name='rolpermiso-detail'),
]