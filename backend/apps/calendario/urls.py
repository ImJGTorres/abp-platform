from django.urls import path

from .views import CalendarioEventoView, CalendarioView

# Incluido en config/urls.py bajo 'api/calendario/'
urlpatterns = [
    path('', CalendarioView.as_view(), name='calendario'),
    path('<str:evento_id>/', CalendarioEventoView.as_view(), name='calendario_evento'),
]
