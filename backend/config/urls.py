"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
# SimpleJWT views importadas para endpoints de refresh y logout (BE-04, BE-05)
# TokenRefreshView: Permite obtener nuevo access token usando refresh token
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from django.views.generic import TemplateView

from apps.usuarios.views import CambiarContrasenaView, LoginView, OlvidarContrasenaView, RecuperarContrasenaView
from apps.roles.views import PermisosAgrupadosView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/usuarios/', include('apps.usuarios.urls')),
    # Endpoint de login (BE-02): POST /api/auth/login/
    # Recibe correo y contraseña, retorna access + refresh tokens
    # Customizado para usar modelo Usuario personalizado
    path('api/auth/login/',   LoginView.as_view(),        name='token_obtain'),
    
    # Endpoint de refresh token (BE-04): POST /api/auth/refresh/
    # Recibe refresh token, retorna nuevo access token
    # Configuración en settings.py SIMPLE_JWT (ACCESS_TOKEN_LIFETIME)
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoint de logout (BE-05): POST /api/auth/logout/
    # Recibe refresh token y lo agrega a blacklist
    # Evita que el token pueda usarse nuevamente
    # Requiere: REST_FRAMEWORK_SIMPLEJWT.token_blacklist en INSTALLED_APPS
    path('api/auth/logout/',  TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/auth/olvidar-contrasena/',  OlvidarContrasenaView.as_view(),  name='olvidar_contrasena'),
    path('api/auth/recuperar-contrasena/', RecuperarContrasenaView.as_view(), name='recuperar_contrasena'),
    path('api/auth/cambiar-contrasena/',   CambiarContrasenaView.as_view(),   name='cambiar_contrasena'),

    path('api/configuracion/', include('apps.configuracion.urls')),
    # Se conectan con las urls de cada modelo.
    # ejemplo: /api/roles/permisos/
    path('api/roles/', include('apps.roles.urls')),

    # BE-07: Permisos agrupados por módulo (para formulario de asignación)
    path('api/permisos/', PermisosAgrupadosView.as_view(), name='permisos-agrupados'),
    path('api/bitacora/', include('apps.bitacora.urls')),  # Endpoint para consultar bitácora del sistema
    path('api/', include('apps.equipos.urls')),
    path('api/cursos/', include('apps.cursos.urls')),
    path('api/proyectos/', include('apps.cursos.proyecto_urls')),

    # SPA: Servir index.html para cualquier ruta que no sea API ni static
    # Excluye /api/ y /static/ usando lookahead negativo en regex
    re_path(r'^(?!api/|static/|django-admin/).*$', TemplateView.as_view(template_name='index.html'), name='frontend'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
