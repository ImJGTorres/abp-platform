from django.urls import path

from .views import CursoDetailView, CursoListCreateView

urlpatterns = [
    path('', CursoListCreateView.as_view(), name='curso-list-create'),
    path('<int:pk>/', CursoDetailView.as_view(), name='curso-detail'),
]