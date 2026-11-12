"""Segunda auditoría de seguridad: IP real, bloqueo de login, sesiones y recuperación de contraseña."""
import hashlib
import re
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import mail
from django.test import RequestFactory
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import _get_ip
from apps.usuarios.models import TokenRecuperacion, Usuario
from tests.factories import UsuarioFactory

LOGIN = '/api/auth/login/'
REFRESH = '/api/auth/refresh/'
CLAVE = 'Correcta-2026-xyz!'


def usuario_con_clave(correo='u@ufps.edu.co', clave=CLAVE):
    u = UsuarioFactory(correo=correo)
    u.set_password(clave)
    u.save()
    return u


def login(correo, clave, ip=None):
    extra = {'HTTP_X_FORWARDED_FOR': ip} if ip else {}
    return APIClient().post(LOGIN, {'correo': correo, 'contrasena': clave}, format='json', **extra)


# --- A-01: IP del cliente -----------------------------------------------------

@pytest.mark.parametrize('xff,remote,esperada', [
    ('1.2.3.4', '10.0.0.1', '1.2.3.4'),
    ('6.6.6.6, 1.2.3.4', '10.0.0.1', '1.2.3.4'),          # el cliente antepone una IP falsa: se ignora
    ('basura', '10.0.0.1', '10.0.0.1'),                   # no es una IP: se usa REMOTE_ADDR
    ('', '10.0.0.1', '10.0.0.1'),
    (None, '10.0.0.1', '10.0.0.1'),
    ('1.2.3.4', 'no-ip', '1.2.3.4'),
])
def test_ip_del_cliente_no_se_deja_falsificar(xff, remote, esperada):
    extra = {'REMOTE_ADDR': remote}
    if xff is not None:
        extra['HTTP_X_FORWARDED_FOR'] = xff
    assert _get_ip(RequestFactory().get('/', **extra)) == esperada


@pytest.mark.django_db
def test_login_con_cabecera_ip_invalida_igual_queda_en_bitacora():
    login('nadie@ufps.edu.co', 'mala', ip='no-es-una-ip')
    assert BitacoraSistema.objects.filter(accion='ACCESS_DENIED', modulo='autenticacion').exists()


@pytest.mark.django_db
def test_el_limite_por_ip_no_se_evade_variando_la_primera_entrada_del_xff():
    for i in range(settings.LOGIN_MAX_INTENTOS_IP):
        assert login(f'x{i}@ufps.edu.co', 'mala', ip=f'9.9.{i}.1, 5.5.5.5').status_code == 401
    assert login('otro@ufps.edu.co', 'mala', ip='7.7.7.7, 5.5.5.5').status_code == 429


# --- A-02: el bloqueo no permite negar servicio a un tercero ------------------

@pytest.mark.django_db
def test_un_tercero_no_bloquea_la_cuenta_desde_su_propia_ip():
    usuario_con_clave('victima@ufps.edu.co')
    for _ in range(settings.LOGIN_MAX_INTENTOS_PAR):
        login('victima@ufps.edu.co', 'mala', ip='1.1.1.1')
    assert login('victima@ufps.edu.co', CLAVE, ip='1.1.1.1').status_code == 429
    assert login('victima@ufps.edu.co', CLAVE, ip='2.2.2.2').status_code == 200


@pytest.mark.django_db
def test_ataque_repartido_entre_ips_termina_bloqueando_el_correo():
    usuario_con_clave('objetivo@ufps.edu.co')
    for i in range(settings.LOGIN_MAX_INTENTOS_CORREO):
        login('objetivo@ufps.edu.co', 'mala', ip=f'3.3.{i}.1')
    assert login('objetivo@ufps.edu.co', CLAVE, ip='4.4.4.4').status_code == 429


@pytest.mark.django_db
def test_correo_inexistente_igual_gasta_tiempo_de_hash():
    with patch('apps.usuarios.views._gastar_tiempo_de_hash') as falso:
        assert login('no-existe@ufps.edu.co', 'x').status_code == 401
    falso.assert_called_once()


@pytest.mark.django_db
def test_login_con_saltos_de_linea_en_el_correo_se_sanea_en_bitacora():
    login('a@ufps.edu.co\nFALSO: login exitoso de admin\r\n' + 'x' * 300, 'mala')
    desc = BitacoraSistema.objects.filter(modulo='autenticacion').latest('id').descripcion
    assert '\n' not in desc and '\r' not in desc
    assert len(desc) < 200


@pytest.mark.django_db
def test_login_con_correo_que_no_es_texto_no_rompe():
    r = APIClient().post(LOGIN, {'correo': 12345, 'contrasena': 'x'}, format='json')
    assert r.status_code == 401


# --- A-03: las sesiones no sobreviven al cambio de contraseña -------------------

@pytest.mark.django_db
def test_cambiar_contrasena_revoca_los_refresh_tokens():
    usuario_con_clave('sesion@ufps.edu.co')
    r = login('sesion@ufps.edu.co', CLAVE)
    refresh, access = r.json()['refresh'], r.json()['access']
    # rota una vez: el refresh nuevo también debe quedar revocado
    nuevo = APIClient().post(REFRESH, {'refresh': refresh}, format='json').json()['refresh']

    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r = cliente.post('/api/auth/cambiar-contrasena/', {
        'password_actual': CLAVE, 'nueva_contrasena': 'Nueva-Clave-9137!', 'confirmar_contrasena': 'Nueva-Clave-9137!'},
        format='json')
    assert r.status_code == 200, r.content
    assert APIClient().post(REFRESH, {'refresh': nuevo}, format='json').status_code == 401
    assert login('sesion@ufps.edu.co', 'Nueva-Clave-9137!').status_code == 200


# --- A-04: la política de contraseñas se aplica ---------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('debil', ['12345678', 'password', 'aaaaaaaa'])
def test_cambiar_contrasena_rechaza_claves_debiles(debil):
    usuario_con_clave('debil@ufps.edu.co')
    access = login('debil@ufps.edu.co', CLAVE).json()['access']
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r = c.post('/api/auth/cambiar-contrasena/', {
        'password_actual': CLAVE, 'nueva_contrasena': debil, 'confirmar_contrasena': debil}, format='json')
    assert r.status_code == 400
    assert Usuario.objects.get(correo='debil@ufps.edu.co').check_password(CLAVE)


# --- A-05 / A-06: recuperación de contraseña --------------------------------------

def _pedir_enlace(correo):
    mail.outbox.clear()
    APIClient().post('/api/auth/olvidar-contrasena/', {'correo': correo}, format='json')
    assert mail.outbox, 'no se envió el correo'
    return re.search(r'recuperar-contrasena(\S+)', mail.outbox[0].body).group(1)


@pytest.mark.django_db
def test_token_de_recuperacion_se_guarda_con_hash_y_viaja_en_el_fragmento():
    u = usuario_con_clave('rec@ufps.edu.co')
    sufijo = _pedir_enlace('rec@ufps.edu.co')
    assert sufijo.startswith('#token=')          # fragmento, no query
    token = sufijo.split('=', 1)[1].rstrip('.')
    guardado = TokenRecuperacion.objects.get(usuario=u).token
    assert token not in guardado and guardado == hashlib.sha256(token.encode()).hexdigest()

    # el hash guardado no sirve como token
    c = APIClient()
    r = c.post('/api/auth/recuperar-contrasena/', {
        'token': guardado, 'nueva_contrasena': 'Nueva-Clave-9137!', 'confirmar_contrasena': 'Nueva-Clave-9137!'},
        format='json')
    assert r.status_code == 400
    # el token real sí, una sola vez
    cuerpo = {'token': token, 'nueva_contrasena': 'Nueva-Clave-9137!', 'confirmar_contrasena': 'Nueva-Clave-9137!'}
    assert c.post('/api/auth/recuperar-contrasena/', cuerpo, format='json').status_code == 200
    assert c.post('/api/auth/recuperar-contrasena/', cuerpo, format='json').status_code == 400


@pytest.mark.django_db
def test_recuperar_contrasena_aplica_politica_y_revoca_sesiones():
    usuario_con_clave('rec2@ufps.edu.co')
    refresh = login('rec2@ufps.edu.co', CLAVE).json()['refresh']
    token = _pedir_enlace('rec2@ufps.edu.co').split('=', 1)[1].rstrip('.')
    c = APIClient()
    debil = c.post('/api/auth/recuperar-contrasena/', {
        'token': token, 'nueva_contrasena': '12345678', 'confirmar_contrasena': '12345678'}, format='json')
    assert debil.status_code == 400
    ok = c.post('/api/auth/recuperar-contrasena/', {
        'token': token, 'nueva_contrasena': 'Nueva-Clave-9137!', 'confirmar_contrasena': 'Nueva-Clave-9137!'},
        format='json')
    assert ok.status_code == 200
    assert APIClient().post(REFRESH, {'refresh': refresh}, format='json').status_code == 401


@pytest.mark.django_db
def test_olvidar_contrasena_limita_correos_por_ip():
    for i in range(15):
        usuario_con_clave(f'masa{i}@ufps.edu.co')
    mail.outbox.clear()
    for i in range(15):
        r = APIClient().post('/api/auth/olvidar-contrasena/', {'correo': f'masa{i}@ufps.edu.co'},
                             format='json', HTTP_X_FORWARDED_FOR='8.8.8.8')
        assert r.status_code == 200      # la respuesta es siempre la misma
    assert len(mail.outbox) == 10


# --- A-14 / A-15: exportaciones y límites generales ---------------------------------

def test_throttling_global_configurado():
    rf = settings.REST_FRAMEWORK
    assert 'rest_framework.throttling.AnonRateThrottle' in rf['DEFAULT_THROTTLE_CLASSES']
    assert 'rest_framework.throttling.UserRateThrottle' in rf['DEFAULT_THROTTLE_CLASSES']
    assert set(rf['DEFAULT_THROTTLE_RATES']) == {'anon', 'user'}


@pytest.mark.django_db
def test_exportaciones_por_hora_tienen_tope():
    from apps.exportaciones.models import Exportacion
    from apps.exportaciones.views import MAX_EXPORTACIONES_POR_HORA
    admin = UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR)
    for _ in range(MAX_EXPORTACIONES_POR_HORA):
        Exportacion.objects.create(id_usuario=admin, tipo_reporte='indicadores', formato='excel',
                                   parametros={}, estado='listo')
    c = APIClient()
    c.force_authenticate(user=admin)
    r = c.post('/api/exportar/reporte/', {'tipo_reporte': 'indicadores', 'formato': 'excel', 'parametros': {}}, format='json')
    assert r.status_code == 429


@pytest.mark.django_db
def test_url_de_descarga_pasa_por_la_vista_autenticada_y_no_por_media():
    admin = UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR)
    c = APIClient()
    c.force_authenticate(user=admin)
    creada = c.post('/api/exportar/reporte/', {'tipo_reporte': 'indicadores', 'formato': 'excel', 'parametros': {}}, format='json').json()
    estado = c.get(f"/api/exportar/{creada['id']}/estado/").json()
    assert estado['estado'] == 'listo'
    assert estado['url_descarga'] == f"/api/exportar/{creada['id']}/descargar/"
    assert c.get(estado['url_descarga']).status_code == 200
    # otro usuario no puede descargar la exportación ajena
    otro = APIClient()
    otro.force_authenticate(user=UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR))
    assert otro.get(estado['url_descarga']).status_code == 404


@pytest.mark.django_db
def test_error_interno_de_exportacion_no_filtra_detalles():
    from apps.exportaciones.models import Exportacion
    from apps.exportaciones.services import generar_exportacion
    admin = UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR)
    exp = Exportacion.objects.create(id_usuario=admin, tipo_reporte='indicadores', formato='excel', parametros={}, estado='generando')
    with patch('apps.exportaciones.services._obtener_datos', side_effect=RuntimeError('SELECT * FROM secreto password=abc')):
        generar_exportacion(exp.id)
    exp.refresh_from_db()
    assert exp.estado == 'error'
    assert 'secreto' not in exp.mensaje_error and 'password' not in exp.mensaje_error


# --- A-10 / A-11: exportaciones con texto de usuario malicioso -----------------------

@pytest.mark.django_db
def test_excel_no_guarda_formulas_escritas_por_usuarios(tmp_path):
    from openpyxl import load_workbook
    from apps.exportaciones.generadores.excel import generar_excel_equipo
    datos = {
        'equipo': {'nombre': '=HYPERLINK("http://malo","x")', 'proyecto_nombre': '=1+1'},
        'total_miembros': 1,
        'miembros': [{'estudiante': {'nombre': '=cmd|calc', 'apellido': '@SUM(A1)', 'codigo': '=2+2', 'rol_interno': ''},
                      'nota_final': 3.0}],
    }
    ruta = tmp_path / 'e.xlsx'
    generar_excel_equipo(datos, str(ruta))
    libro = load_workbook(ruta)
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows():
            for celda in fila:
                assert celda.data_type != 'f', (hoja.title, celda.coordinate, celda.value)


def test_pdf_con_marcado_en_nombres_no_rompe_la_exportacion(tmp_path):
    from apps.exportaciones.generadores.pdf import generar_pdf_equipo
    datos = {
        'equipo': {'nombre': 'A<b>B</i><img src="http://x/y.png"/>', 'proyecto_nombre': '<font size=900>P'},
        'total_miembros': 0, 'miembros': [],
    }
    ruta = tmp_path / 'e.pdf'
    generar_pdf_equipo(datos, str(ruta))
    assert ruta.read_bytes().startswith(b'%PDF')


# --- A-21: los seeds de datos demo no corren en producción ---------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('comando', ['seed_hu040_demo', 'seed_hu041_demo', 'seed_hu042_demo', 'seed_hu043_demo'])
def test_seeds_demo_se_niegan_con_debug_apagado(comando, settings):
    from django.core.management import call_command
    from django.core.management.base import CommandError
    settings.DEBUG = False
    antes = Usuario.objects.count()
    with pytest.raises(CommandError):
        call_command(comando)
    assert Usuario.objects.count() == antes
