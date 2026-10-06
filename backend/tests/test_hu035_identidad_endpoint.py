"""
HU-035 — Endpoint GET/PUT /api/configuracion/identidad/ (SCRUM-607).
"""
import io
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import IdentidadInstitucional, ParametroSistema
from tests.factories import AdminFactory, DocenteFactory

URL = '/api/configuracion/identidad/'


def _png(nombre='logo.png', tamano=(50, 50)):
    buf = io.BytesIO()
    Image.new('RGB', tamano, 'red').save(buf, 'PNG')
    return SimpleUploadedFile(nombre, buf.getvalue(), content_type='image/png')


def _datos(**extra):
    return {'nombre_institucion': 'Universidad Francisco de Paula Santander',
            'programa_academico': 'Ingeniería de Sistemas', **extra}


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def admin(cliente):
    usuario = AdminFactory()
    cliente.force_authenticate(user=usuario)
    return usuario


@pytest.mark.django_db
def test_get_autenticado_devuelve_valores_por_defecto(cliente):
    cliente.force_authenticate(user=DocenteFactory())
    r = cliente.get(URL)
    assert r.status_code == 200
    assert r.data['nombre_institucion'] == 'UFPS — Plataforma ABP'
    assert r.data['programa_academico'] == 'Ingeniería de Sistemas'
    assert r.data['logotipo'] is None
    assert 'fecha_actualizacion' in r.data


@pytest.mark.django_db
def test_get_sin_autenticar_retorna_401(cliente):
    assert cliente.get(URL).status_code == 401


@pytest.mark.django_db
def test_put_admin_guarda_logo_usuario_y_bitacora(cliente, admin):
    r = cliente.put(URL, _datos(logotipo=_png()), format='multipart')

    assert r.status_code == 200
    assert r.data['nombre_institucion'] == 'Universidad Francisco de Paula Santander'
    assert r.data['logotipo'].startswith('/media/identidad/')  # ruta de media para buildMediaUrl()

    identidad = IdentidadInstitucional.objects.get(pk=1)
    assert identidad.id_usuario_actualiza_id == admin.id
    assert os.path.isfile(identidad.logotipo.path)

    evento = BitacoraSistema.objects.filter(accion='UPDATE', modulo='configuracion').last()
    assert evento.descripcion == ('Identidad institucional actualizada: '
                                  'nombre_institucion, logotipo')

    # Al recargar (GET) se ven los datos guardados
    assert cliente.get(URL).data == r.data


@pytest.mark.django_db
def test_put_docente_retorna_403(cliente):
    cliente.force_authenticate(user=DocenteFactory())
    r = cliente.put(URL, _datos(), format='multipart')
    assert r.status_code == 403
    assert not IdentidadInstitucional.objects.filter(
        nombre_institucion='Universidad Francisco de Paula Santander').exists()


@pytest.mark.django_db
def test_put_logo_de_3_mb_retorna_400(cliente, admin):
    grande = SimpleUploadedFile('logo.png', b'0' * (3 * 1024 * 1024), content_type='image/png')
    r = cliente.put(URL, _datos(logotipo=grande), format='multipart')
    assert r.status_code == 400
    assert r.data['logotipo'] == ['El logotipo no puede superar 2 MB.']


@pytest.mark.django_db
def test_put_logo_gif_retorna_400(cliente, admin):
    gif = SimpleUploadedFile('logo.gif', b'GIF89a', content_type='image/gif')
    r = cliente.put(URL, _datos(logotipo=gif), format='multipart')
    assert r.status_code == 400
    assert r.data['logotipo'] == ['Solo se permiten archivos PNG o JPG.']


@pytest.mark.django_db
def test_put_sin_nombre_retorna_400_por_campo(cliente, admin):
    r = cliente.put(URL, {'programa_academico': 'Sistemas'}, format='multipart')
    assert r.status_code == 400
    assert 'nombre_institucion' in r.data


@pytest.mark.django_db
def test_reemplazar_logo_borra_el_anterior_y_sin_logo_lo_conserva(cliente, admin):
    cliente.put(URL, _datos(logotipo=_png('uno.png')), format='multipart')
    anterior = IdentidadInstitucional.objects.get(pk=1).logotipo.path

    cliente.put(URL, _datos(logotipo=_png('dos.png')), format='multipart')
    nuevo = IdentidadInstitucional.objects.get(pk=1).logotipo.path
    assert not os.path.exists(anterior)
    assert os.path.isfile(nuevo)

    # PUT sin logotipo: conserva el actual
    r = cliente.put(URL, _datos(programa_academico='Otro programa'), format='multipart')
    assert r.status_code == 200
    assert IdentidadInstitucional.objects.get(pk=1).logotipo.path == nuevo


@pytest.mark.django_db
def test_patch_de_parametros_sigue_funcionando(cliente, admin):
    ParametroSistema.objects.create(clave='max_estudiantes_por_equipo', valor='6',
                                    categoria='general', tipo_dato='integer')
    r = cliente.patch('/api/configuracion/max_estudiantes_por_equipo/', {'valor': '8'}, format='json')
    assert r.status_code == 200
    assert ParametroSistema.objects.get(clave='max_estudiantes_por_equipo').valor == '8'


# ── Parámetros decimales y categoría 'rendimiento' (migraciones 0004 y 0007) ─

@pytest.mark.django_db
@pytest.mark.parametrize('clave,categoria,tipo,valor,esperado', [
    ('umbral_nota_alerta', 'general', 'float', '3.6', 3.6),
    ('umbral_nota_bajo_rendimiento', 'rendimiento', 'float', '2.8', 2.8),
    ('umbral_porcentaje_actividades_incumplidas', 'rendimiento', 'integer', '40', 40),
])
def test_patch_umbrales_del_semaforo(cliente, admin, clave, categoria, tipo, valor, esperado):
    ParametroSistema.objects.update_or_create(
        clave=clave, defaults={'valor': '1', 'categoria': categoria, 'tipo_dato': tipo})
    r = cliente.patch(f'/api/configuracion/{clave}/', {'valor': valor}, format='json')
    assert r.status_code == 200, r.data
    assert r.data['valor_casteado'] == esperado


@pytest.mark.django_db
@pytest.mark.parametrize('valor', ['abc', '-1', 'nan'])
def test_patch_decimal_invalido_retorna_400(cliente, admin, valor):
    ParametroSistema.objects.update_or_create(
        clave='umbral_nota_alerta', defaults={'valor': '3.5', 'categoria': 'general', 'tipo_dato': 'float'})
    r = cliente.patch('/api/configuracion/umbral_nota_alerta/', {'valor': valor}, format='json')
    assert r.status_code == 400


@pytest.mark.django_db
def test_semaforo_usa_el_umbral_editado(cliente, admin):
    from apps.reportes.semaforo import clasificar_semaforo
    ParametroSistema.objects.update_or_create(
        clave='umbral_nota_alerta', defaults={'valor': '3.5', 'categoria': 'general', 'tipo_dato': 'float'})
    assert clasificar_semaforo(3.7, 0) == 'verde'
    cliente.patch('/api/configuracion/umbral_nota_alerta/', {'valor': '4.0'}, format='json')
    assert clasificar_semaforo(3.7, 0) == 'amarillo'
