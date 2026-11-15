"""Pruebas de sesión y configuración derivadas de la auditoría (NUE-10, 11, 12, 19, 27)."""
import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioUpdateSerializer
from tests.factories import UsuarioFactory

LOGIN = '/api/auth/login/'


def _login(correo, contrasena):
    return APIClient().post(LOGIN, {'correo': correo, 'contrasena': contrasena}, format='json')


@pytest.mark.django_db
def test_nue10_login_se_bloquea_tras_varios_fallos_y_se_reinicia_con_exito():
    usuario = UsuarioFactory(correo='fuerza@ufps.edu.co')
    usuario.set_password('Correcta123!')
    usuario.save()
    for _ in range(settings.LOGIN_MAX_INTENTOS_PAR):
        assert _login('fuerza@ufps.edu.co', 'mala').status_code == 401
    # superado el límite: ni siquiera la contraseña correcta entra
    assert _login('fuerza@ufps.edu.co', 'Correcta123!').status_code == 429
    # otro correo no se ve afectado
    otro = UsuarioFactory(correo='otro@ufps.edu.co')
    otro.set_password('Correcta123!')
    otro.save()
    assert _login('otro@ufps.edu.co', 'Correcta123!').status_code == 200


@pytest.mark.django_db
def test_nue10_un_login_correcto_reinicia_el_contador():
    usuario = UsuarioFactory(correo='reinicia@ufps.edu.co')
    usuario.set_password('Correcta123!')
    usuario.save()
    for _ in range(settings.LOGIN_MAX_INTENTOS_PAR - 1):
        _login('reinicia@ufps.edu.co', 'mala')
    assert _login('reinicia@ufps.edu.co', 'Correcta123!').status_code == 200
    for _ in range(settings.LOGIN_MAX_INTENTOS_PAR - 1):
        assert _login('reinicia@ufps.edu.co', 'mala').status_code == 401


@pytest.mark.django_db
def test_nue11_refresh_de_usuario_desactivado_es_rechazado():
    usuario = UsuarioFactory()
    refresh = RefreshToken()
    refresh['user_id'] = usuario.id
    url = reverse('token_refresh')
    assert APIClient().post(url, {'refresh': str(refresh)}, format='json').status_code == 200

    usuario.estado = Usuario.Estado.INACTIVO
    usuario.save()
    assert APIClient().post(url, {'refresh': str(refresh)}, format='json').status_code == 401


@pytest.mark.django_db
def test_nue11_access_token_de_usuario_desactivado_no_entra_a_vistas_por_defecto():
    usuario = UsuarioFactory()
    refresh = RefreshToken()
    refresh['user_id'] = usuario.id
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    assert cliente.get('/api/usuarios/perfil/').status_code == 200

    usuario.estado = Usuario.Estado.INACTIVO
    usuario.save()
    assert cliente.get('/api/usuarios/perfil/').status_code == 401


def test_nue12_cors_no_abre_todos_los_origenes_en_produccion():
    # En la suite DEBUG es False, igual que en producción
    assert settings.DEBUG is False
    assert settings.CORS_ALLOW_ALL_ORIGINS is False


def test_nue19_https_endurecido_fuera_de_desarrollo():
    from django.core.management import call_command
    from io import StringIO
    from django.test.utils import override_settings

    with override_settings(
        SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000,
        SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, DEBUG=False,
    ):
        salida = StringIO()
        call_command('check', '--deploy', stdout=salida, stderr=salida)
    texto = salida.getvalue()
    for codigo in ('W004', 'W008', 'W012', 'W016'):  # HSTS, SSL redirect, cookies de sesión y CSRF
        assert f'security.{codigo}' not in texto, texto
    assert settings.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')


def test_nue27_localizacion_colombia():
    assert settings.LANGUAGE_CODE == 'es-co'
    assert settings.TIME_ZONE == 'America/Bogota'


@pytest.mark.parametrize('nombre,valido', [
    ("Ana-María", True), ("O'Connor", True), ("José Luis", True), ("Núñez", True),
    ("Vega2", False), ("Ana--", False), ("-Ana", False), ("A", False), ("Ana_", False),
])
def test_nue27_validador_de_nombres(nombre, valido):
    s = UsuarioUpdateSerializer(data={'nombre': nombre}, partial=True)
    assert s.is_valid() is valido, s.errors


@pytest.mark.parametrize('foto,valida', [
    ('', True), ('/media/fotos_perfil/5_abc123.png', True),
    ('https://cdn.example.com/f.jpg', False), ('javascript:alert(1)', False), ('cualquier texto', False),
    ('/media/fotos_perfil/../../db.sqlite3', False), ('/media/fotos_perfil/a/../b.png', False),
])
def test_nue27_validador_de_foto_perfil(foto, valida):
    s = UsuarioUpdateSerializer(data={'foto_perfil': foto}, partial=True)
    assert s.is_valid() is valida, s.errors


def test_nue13_csp_en_respuestas_fuera_de_admin(settings):
    settings.CSP_ENABLED = True
    resp = APIClient().get('/api/usuarios/perfil/')  # 401, pero pasa por el middleware
    csp = resp['Content-Security-Policy']
    assert "script-src 'self'" in csp and "object-src 'none'" in csp and "frame-ancestors 'none'" in csp


def test_nue13_csp_no_se_aplica_al_admin_de_django(settings):
    from django.http import HttpResponse
    from django.test import RequestFactory

    from config.csp import CSPMiddleware

    settings.CSP_ENABLED = True
    middleware = CSPMiddleware(lambda request: HttpResponse('ok'))
    assert 'Content-Security-Policy' not in middleware(RequestFactory().get('/django-admin/login/'))
    assert 'Content-Security-Policy' in middleware(RequestFactory().get('/'))


def test_nue13_csp_desactivable_en_desarrollo(settings):
    settings.CSP_ENABLED = False
    assert 'Content-Security-Policy' not in APIClient().get('/api/usuarios/perfil/')
