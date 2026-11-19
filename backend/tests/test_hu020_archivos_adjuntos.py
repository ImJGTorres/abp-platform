"""HU-020 — Archivos adjuntos de entregables (regresión, Sprint 7 / SCRUM-658).

El archivo existía vacío (HAL-S7-10). Cubre el ciclo completo: subir en borrador, listar,
borrar, quién puede hacer cada cosa, tamaño máximo, extensión y que la respuesta no exponga
la ruta interna. La validación por firma está en test_seguridad_propiedad.py.
"""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, Proyecto
from apps.entregables.models import ArchivoAdjunto, Entregable
from tests.factories import (
    AdminFactory, CursoFactory, DocenteFactory, EquipoFactory, FaseProyectoFactory,
    MiembroEquipoFactory, UsuarioFactory,
)

PDF = b'%PDF-1.4 informe'


def cli(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


@pytest.fixture
def esc(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '10', 'categoria': ParametroSistema.Categoria.GENERAL,
                  'tipo_dato': ParametroSistema.TipoDato.INTEGER})
    dueno = DocenteFactory()
    curso = CursoFactory(id_docente=dueno, usuario_creo=dueno)
    proyecto = Proyecto.objects.create(
        nombre='P', id_curso=curso, fecha_inicio=date(2026, 2, 1),
        fecha_fin_estimada=date(2026, 5, 31), estado=Proyecto.Estado.EN_EJECUCION)
    equipo = EquipoFactory(proyecto=proyecto)
    otro_equipo = EquipoFactory(proyecto=proyecto)
    miembro, companero_otro_equipo = UsuarioFactory(), UsuarioFactory()
    MiembroEquipoFactory(equipo=equipo, usuario=miembro)
    MiembroEquipoFactory(equipo=otro_equipo, usuario=companero_otro_equipo)
    fase = FaseProyectoFactory(id_proyecto=proyecto)
    act = Actividad.objects.create(id_fase=fase, nombre='A', fecha_limite=date(2026, 3, 1),
                                   prioridad='media', estado='pendiente', id_equipo_asignado=equipo)
    ent = Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='E', descripcion='d',
                                    tipo='documento', estado='borrador')
    return dict(dueno=dueno, miembro=miembro, companero_otro_equipo=companero_otro_equipo, ent=ent,
                docente_ajeno=DocenteFactory(), estudiante_ajeno=UsuarioFactory(), admin=AdminFactory(),
                tmp=tmp_path)


def subir(usuario, ent, nombre='informe.pdf', contenido=PDF, tipo='application/pdf', **extra):
    return cli(usuario).post(f'/api/entregables/{ent.id}/archivos/',
                             {'archivo': SimpleUploadedFile(nombre, contenido, content_type=tipo)},
                             format='multipart', **extra)


def test_cp01_miembro_sube_adjunto_en_borrador(esc):
    r = subir(esc['miembro'], esc['ent'])
    assert r.status_code == 201, r.content
    datos = r.json()
    assert datos['nombre_original'] == 'informe.pdf'
    assert datos['tipo_mime'] == 'application/pdf'
    assert 'ruta' not in datos and 'nombre_almacenado' not in datos
    adj = ArchivoAdjunto.objects.get(pk=datos['id'])
    assert (esc['tmp'] / adj.ruta).exists()


def test_cp02_subida_queda_en_bitacora_con_ip_real(esc):
    r = subir(esc['miembro'], esc['ent'], HTTP_X_FORWARDED_FOR='181.50.1.20', REMOTE_ADDR='10.0.0.1')
    assert r.status_code == 201
    registro = BitacoraSistema.objects.filter(modulo='Archivos').latest('id')
    assert str(registro.ip_origen) == '181.50.1.20'
    assert 'informe.pdf' in registro.descripcion


@pytest.mark.parametrize('actor', ['companero_otro_equipo', 'estudiante_ajeno', 'docente_ajeno', 'dueno'])
def test_cp03_solo_miembros_del_equipo_suben(esc, actor):
    assert subir(esc[actor], esc['ent']).status_code == 403
    assert not ArchivoAdjunto.objects.exists()


def test_cp04_no_se_sube_a_entregable_enviado(esc):
    esc['ent'].estado = 'enviado'
    esc['ent'].save(update_fields=['estado'])
    assert subir(esc['miembro'], esc['ent']).status_code == 400


def test_cp05_extension_no_permitida(esc):
    r = subir(esc['miembro'], esc['ent'], nombre='script.exe', contenido=b'MZ\x90\x00', tipo='application/octet-stream')
    assert r.status_code == 400
    assert 'formato' in str(r.json()).lower()


def test_cp06_archivo_mayor_al_maximo(esc, settings):
    settings.MAX_UPLOAD_SIZE_BYTES = 1024
    r = subir(esc['miembro'], esc['ent'], contenido=PDF + b'0' * 2048)
    assert r.status_code == 400
    assert 'tamaño' in str(r.json()).lower()


@pytest.mark.parametrize('actor,codigo', [
    ('miembro', 200), ('dueno', 200), ('admin', 200), ('companero_otro_equipo', 200),
    ('estudiante_ajeno', 403), ('docente_ajeno', 403),
])
def test_cp07_quien_lista_los_adjuntos(esc, actor, codigo):
    subir(esc['miembro'], esc['ent'])
    r = cli(esc[actor]).get(f"/api/entregables/{esc['ent'].id}/archivos/")
    assert r.status_code == codigo
    if codigo == 200:
        assert [a['nombre_original'] for a in r.json()] == ['informe.pdf']


@pytest.mark.parametrize('actor,codigo', [
    ('miembro', 204), ('dueno', 204), ('admin', 204),
    ('companero_otro_equipo', 403), ('estudiante_ajeno', 403), ('docente_ajeno', 403),
])
def test_cp08_quien_borra_un_adjunto(esc, actor, codigo):
    adj_id = subir(esc['miembro'], esc['ent']).json()['id']
    assert cli(esc[actor]).delete(f'/api/archivos/{adj_id}/').status_code == codigo
    assert ArchivoAdjunto.objects.filter(pk=adj_id).exists() is (codigo != 204)


def test_cp09_no_se_borra_adjunto_de_entregable_enviado(esc):
    adj_id = subir(esc['miembro'], esc['ent']).json()['id']
    esc['ent'].estado = 'enviado'
    esc['ent'].save(update_fields=['estado'])
    assert cli(esc['miembro']).delete(f'/api/archivos/{adj_id}/').status_code == 400
    assert ArchivoAdjunto.objects.filter(pk=adj_id).exists()


def test_cp10_nombre_guardado_no_viene_del_cliente(esc):
    r = subir(esc['miembro'], esc['ent'], nombre='../../evil.pdf')
    assert r.status_code == 201
    adj = ArchivoAdjunto.objects.get(pk=r.json()['id'])
    assert '..' not in adj.ruta and adj.ruta.startswith('entregables/archivos/')
    assert not (esc['tmp'].parent / 'evil.pdf').exists()
