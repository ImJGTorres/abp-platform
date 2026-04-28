from django.urls import path

from .views import ProyectoDetailView

urlpatterns = [
    # GET/PUT/PATCH /api/proyectos/<pk>/
    path('<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),
]