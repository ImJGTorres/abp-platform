from django.urls import path

from .views import MuroAnunciosView

# Incluido en config/urls.py bajo 'api/' (antes de api/cursos/ y api/proyectos/)
urlpatterns = [
    path('cursos/<int:curso_id>/anuncios/', MuroAnunciosView.as_view(), name='anuncios_curso'),
    path('proyectos/<int:proyecto_id>/anuncios/', MuroAnunciosView.as_view(), name='anuncios_proyecto'),
]
