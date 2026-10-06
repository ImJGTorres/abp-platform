"""
HU-035 — Pruebas de regresión de la identidad institucional (SCRUM-609).

Complementa test_hu035_identidad.py (Nicole, servicio) y
test_hu035_identidad_endpoint.py (Gabriel, endpoint) con:
  - criterios de aceptación de GET/PUT /api/configuracion/identidad/
    (permisos por rol, tipo y tamaño del logotipo, bitácora);
  - obtener_identidad() devuelve lo guardado por el PUT;
  - los demás parámetros del sistema (GET /api/configuracion/ y
    PATCH /api/configuracion/<clave>/) no se ven afectados.

No usa Pillow: el PNG de prueba se arma con bytes fijos.
"""
import struct
import zlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.cache import invalidar_cache_parametros
from apps.configuracion.identidad import obtener_identidad
from apps.configuracion.models import IdentidadInstitucional, ParametroSistema
from tests.factories import AdminFactory, DocenteFactory, UsuarioFactory

URL = '/api/configuracion/identidad/'
URL_PARAMETROS = '/api/configuracion/'
DOS_MB = 2 * 1024 * 1024


def _png_bytes():
    """PNG válido de 1x1 píxel."""
    def chunk(tipo, datos):
        return (struct.pack('>I', len(datos)) + tipo + datos
                + struct.pack('>I', zlib.crc32(tipo + datos) & 0xffffffff))
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\x00\x00')
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')


def _archivo(nombre='logo.png', tamano=None, contenido=None, content_type='image/png'):
    datos = contenido if contenido is not None else _png_bytes()
    if tamano is not None:
        datos = datos + b'\x00' * (tamano - len(datos))
    return SimpleUploadedFile(nombre, datos, content_type=content_type)


def _datos(**extra):
    return {'nombre_institucion': 'Universidad Francisco de Paula Santander',
            'programa_academico': 'Ingeniería de Sistemas', **extra}


@pytest.fixture(autouse=True)
def entorno(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    # El GET de parámetros usa caché en memoria; se limpia para no arrastrar datos entre pruebas
    invalidar_cache_parametros()
    yield
    invalidar_cache_parametros()


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def admin(cliente):
    usuario = AdminFactory()
    cliente.force_authenticate(user=usuario)
    return usuario


@pytest.fixture
def parametros(db):
    """Parámetros del sistema que ya existían antes de HU-035."""
    filas = [
        ('max_estudiantes_por_equipo', '6', 'general', 'integer'),
        ('umbral_nota_bajo_rendimiento', '3.0', 'rendimiento', 'float'),
        ('umbral_porcentaje_actividades_incumplidas', '50', 'rendimiento', 'integer'),
    ]
    for clave, valor, categoria, tipo in filas:
        ParametroSistema.objects.update_or_create(
            clave=clave, defaults={'valor': valor, 'categoria': categoria, 'tipo_dato': tipo})


def _claves(data):
    return {(categoria, p['clave'], p['valor']) for categoria, lista in data.items() for p in lista}


# ── GET ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['administrador', 'director', 'docente', 'lider_equipo', 'estudiante'])
def test_get_autenticado_responde_200_para_todos_los_roles(cliente, rol):
    cliente.force_authenticate(user=UsuarioFactory(tipo_rol=rol))
    r = cliente.get(URL)
    assert r.status_code == 200
    assert set(r.data) == {'nombre_institucion', 'programa_academico', 'logotipo', 'fecha_actualizacion'}


# ── PUT: permisos ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_put_admin_con_logo_png_responde_200_y_registra_bitacora(cliente, admin):
    r = cliente.put(URL, _datos(logotipo=_archivo()), format='multipart')

    assert r.status_code == 200, r.data
    assert r.data['nombre_institucion'] == 'Universidad Francisco de Paula Santander'
    assert r.data['logotipo'].startswith('/media/identidad/')
    evento = BitacoraSistema.objects.filter(
        modulo='configuracion', accion=BitacoraSistema.Accion.UPDATE,
        descripcion__startswith='Identidad institucional actualizada',
    ).latest('fecha_hora')
    assert 'logotipo' in evento.descripcion
    assert evento.id_usuario_id == admin.id


@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['director', 'lider_equipo', 'estudiante'])
def test_put_roles_no_admin_retorna_403(cliente, rol):
    cliente.force_authenticate(user=UsuarioFactory(tipo_rol=rol))
    r = cliente.put(URL, _datos(), format='multipart')
    assert r.status_code == 403
    assert IdentidadInstitucional.obtener().nombre_institucion == IdentidadInstitucional.NOMBRE_INSTITUCION_DEFECTO


@pytest.mark.django_db
def test_put_docente_retorna_403_y_no_registra_bitacora(cliente):
    cliente.force_authenticate(user=DocenteFactory())
    r = cliente.put(URL, _datos(logotipo=_archivo()), format='multipart')
    assert r.status_code == 403
    assert not BitacoraSistema.objects.filter(descripcion__startswith='Identidad institucional').exists()


@pytest.mark.django_db
def test_put_sin_autenticar_retorna_401(cliente):
    assert cliente.put(URL, _datos(), format='multipart').status_code == 401


# ── PUT: validación del logotipo ───────────────────────────────────────────

@pytest.mark.django_db
def test_put_logo_de_exactamente_2_mb_se_acepta(cliente, admin):
    r = cliente.put(URL, _datos(logotipo=_archivo(tamano=DOS_MB)), format='multipart')
    assert r.status_code == 200, r.data


@pytest.mark.django_db
def test_put_logo_mayor_a_2_mb_retorna_400(cliente, admin):
    r = cliente.put(URL, _datos(logotipo=_archivo(tamano=DOS_MB + 1)), format='multipart')
    assert r.status_code == 400
    assert 'logotipo' in r.data
    assert not IdentidadInstitucional.obtener().logotipo


@pytest.mark.django_db
def test_put_archivo_exe_retorna_400(cliente, admin):
    exe = _archivo('instalador.exe', contenido=b'MZ\x90\x00' + b'\x00' * 60,
                   content_type='application/x-msdownload')
    r = cliente.put(URL, _datos(logotipo=exe), format='multipart')
    assert r.status_code == 400
    assert 'logotipo' in r.data
    assert not IdentidadInstitucional.obtener().logotipo


@pytest.mark.django_db
@pytest.mark.parametrize('nombre', ['logo.jpg', 'logo.jpeg', 'LOGO.PNG'])
def test_put_extensiones_permitidas_sin_importar_mayusculas(cliente, admin, nombre):
    r = cliente.put(URL, _datos(logotipo=_archivo(nombre, content_type='image/jpeg')), format='multipart')
    assert r.status_code == 200, r.data


@pytest.mark.django_db
def test_put_exe_renombrado_a_png_retorna_400(cliente, admin):
    falso = _archivo('logo.png', contenido=b'MZ\x90\x00' + b'\x00' * 60)
    r = cliente.put(URL, _datos(logotipo=falso), format='multipart')
    assert r.status_code == 400


# ── obtener_identidad() tras el PUT ────────────────────────────────────────

@pytest.mark.django_db
def test_obtener_identidad_devuelve_los_valores_del_put(cliente, admin):
    r = cliente.put(URL, _datos(nombre_institucion='UFPS Cúcuta', programa_academico='Ing. de Sistemas',
                                logotipo=_archivo()), format='multipart')
    assert r.status_code == 200, r.data

    identidad = obtener_identidad()
    assert identidad['nombre_institucion'] == 'UFPS Cúcuta'
    assert identidad['programa_academico'] == 'Ing. de Sistemas'
    assert identidad['logotipo_url'] == r.data['logotipo']
    assert identidad['logotipo_path'] is not None
    with open(identidad['logotipo_path'], 'rb') as f:
        assert f.read() == _png_bytes()


@pytest.mark.django_db
def test_varios_put_mantienen_un_solo_registro(cliente, admin):
    for nombre in ('Primera', 'Segunda', 'Tercera'):
        assert cliente.put(URL, _datos(nombre_institucion=nombre), format='multipart').status_code == 200
    assert IdentidadInstitucional.objects.count() == 1
    assert obtener_identidad()['nombre_institucion'] == 'Tercera'


@pytest.mark.django_db
def test_put_rechazado_no_modifica_la_identidad_guardada(cliente, admin):
    cliente.put(URL, _datos(nombre_institucion='Valida', logotipo=_archivo()), format='multipart')
    antes = obtener_identidad()

    r = cliente.put(URL, _datos(nombre_institucion='No debe quedar',
                                logotipo=_archivo('virus.exe')), format='multipart')
    assert r.status_code == 400
    assert obtener_identidad() == antes


# ── Regresión: los demás parámetros del sistema ────────────────────────────

@pytest.mark.django_db
def test_get_parametros_lista_lo_mismo_antes_y_despues_del_put(cliente, admin, parametros):
    antes = cliente.get(URL_PARAMETROS)
    assert antes.status_code == 200

    assert cliente.put(URL, _datos(logotipo=_archivo()), format='multipart').status_code == 200
    invalidar_cache_parametros()

    despues = cliente.get(URL_PARAMETROS)
    assert despues.status_code == 200
    assert _claves(despues.data) == _claves(antes.data)
    assert ('general', 'max_estudiantes_por_equipo', '6') in _claves(despues.data)
    # La identidad no se guarda como parámetro
    assert 'identidad' not in {p['clave'] for lista in despues.data.values() for p in lista}


@pytest.mark.django_db
def test_patch_de_parametro_sigue_funcionando_despues_del_put(cliente, admin, parametros):
    cliente.put(URL, _datos(nombre_institucion='UFPS'), format='multipart')

    r = cliente.patch(f'{URL_PARAMETROS}max_estudiantes_por_equipo/', {'valor': '8'}, format='json')
    assert r.status_code == 200, r.data
    assert ParametroSistema.objects.get(clave='max_estudiantes_por_equipo').valor == '8'
    # Y el PATCH no toca la identidad
    assert obtener_identidad()['nombre_institucion'] == 'UFPS'


@pytest.mark.django_db
def test_patch_de_clave_inexistente_sigue_en_404(cliente, admin, parametros):
    r = cliente.patch(f'{URL_PARAMETROS}no_existe/', {'valor': '1'}, format='json')
    assert r.status_code == 404


@pytest.mark.django_db
def test_get_parametros_devuelve_parametros_agrupados_por_categoria(cliente, admin, parametros):
    r = cliente.get(URL_PARAMETROS)
    assert r.status_code == 200
    assert {'general', 'rendimiento'} <= set(r.data)
    assert ('general', 'max_estudiantes_por_equipo', '6') in _claves(r.data)


@pytest.mark.django_db
def test_get_parametros_sigue_restringido_al_administrador(cliente, parametros):
    cliente.force_authenticate(user=DocenteFactory())
    assert cliente.get(URL_PARAMETROS).status_code == 403


@pytest.mark.django_db
def test_patch_parametro_sigue_restringido_al_administrador(cliente, parametros):
    cliente.force_authenticate(user=DocenteFactory())
    r = cliente.patch(f'{URL_PARAMETROS}max_estudiantes_por_equipo/', {'valor': '9'}, format='json')
    assert r.status_code == 403
    assert ParametroSistema.objects.get(clave='max_estudiantes_por_equipo').valor == '6'
