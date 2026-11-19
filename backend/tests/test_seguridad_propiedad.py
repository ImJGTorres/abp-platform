"""Segunda auditoría de seguridad: un docente solo opera sobre sus propios cursos/proyectos.

Cada caso usa un docente ajeno (otro curso) y un estudiante ajeno; el dueño debe poder operar.
"""
from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, CursoEstudiante, Proyecto
from apps.entregables.models import Entregable
from apps.equipos.models import Equipo, MiembroEquipo
from apps.evaluacion.models import Rubrica
from tests.factories import (
    AdminFactory, CursoFactory, DocenteFactory, EquipoFactory, FaseProyectoFactory,
    MiembroEquipoFactory, UsuarioFactory,
)


def cli(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _proyecto(docente):
    curso = CursoFactory(id_docente=docente, usuario_creo=docente)
    return Proyecto.objects.create(
        nombre='P', id_curso=curso, fecha_inicio=date(2026, 2, 1),
        fecha_fin_estimada=date(2026, 5, 31), estado=Proyecto.Estado.EN_EJECUCION)


@pytest.fixture
def esc(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '10', 'categoria': ParametroSistema.Categoria.GENERAL,
                  'tipo_dato': ParametroSistema.TipoDato.INTEGER})
    dueno, ajeno = DocenteFactory(), DocenteFactory()
    proyecto = _proyecto(dueno)
    equipo = EquipoFactory(proyecto=proyecto, cupo_maximo=4)
    miembro = UsuarioFactory()
    MiembroEquipoFactory(equipo=equipo, usuario=miembro)
    CursoEstudiante.objects.create(curso=proyecto.id_curso, estudiante=miembro)
    fase = FaseProyectoFactory(id_proyecto=proyecto)
    act = Actividad.objects.create(
        id_fase=fase, nombre='A', fecha_limite=date(2026, 3, 1), prioridad='media',
        estado='pendiente', id_equipo_asignado=equipo)
    ent = Entregable.objects.create(
        id_actividad=act, id_equipo=equipo, titulo='E', descripcion='d', tipo='documento', estado='enviado')
    otro_proyecto = _proyecto(ajeno)
    return dict(dueno=dueno, ajeno=ajeno, proyecto=proyecto, equipo=equipo, miembro=miembro,
                fase=fase, act=act, ent=ent, otro_proyecto=otro_proyecto,
                estudiante_ajeno=UsuarioFactory(), admin=AdminFactory())


# --- S-01 / S-02: entregables ------------------------------------------------

@pytest.mark.parametrize('accion', ['aprobar', 'rechazar'])
def test_docente_ajeno_no_valida_entregables(esc, accion):
    url = f"/api/entregables/{esc['ent'].id}/{accion}/"
    r = cli(esc['ajeno']).patch(url, {'retroalimentacion': 'x'}, format='json')
    assert r.status_code == 403, r.content
    esc['ent'].refresh_from_db()
    assert esc['ent'].estado == 'enviado'


def test_docente_dueno_valida_entregable(esc):
    r = cli(esc['dueno']).patch(f"/api/entregables/{esc['ent'].id}/aprobar/", {'retroalimentacion': 'ok'}, format='json')
    assert r.status_code == 200, r.content


def test_docente_ajeno_no_ve_pendientes(esc):
    url = f"/api/proyectos/{esc['proyecto'].id}/entregables-pendientes/"
    assert cli(esc['ajeno']).get(url).status_code == 403
    assert cli(esc['dueno']).get(url).status_code == 200


def test_no_se_adjuntan_archivos_a_entregables_enviados(esc):
    from django.core.files.uploadedfile import SimpleUploadedFile
    archivo = SimpleUploadedFile('a.pdf', b'%PDF-1.4 x', content_type='application/pdf')
    r = cli(esc['miembro']).post(f"/api/entregables/{esc['ent'].id}/archivos/", {'archivo': archivo}, format='multipart')
    assert r.status_code == 400, r.content


# --- S-03: reportes ----------------------------------------------------------

def test_docente_ajeno_no_ve_reportes(esc):
    for url in (
        f"/api/reportes/proyecto/{esc['proyecto'].id}/",
        f"/api/reportes/equipo/{esc['equipo'].id}/estudiantes/",
        f"/api/reportes/curso/{esc['proyecto'].id_curso_id}/",
        f"/api/reportes/estudiante/{esc['miembro'].id}/proyecto/{esc['proyecto'].id}/",
        f"/api/reportes/estudiantes/{esc['miembro'].id}/rendimiento/",
    ):
        assert cli(esc['ajeno']).get(url).status_code == 403, url
        assert cli(esc['dueno']).get(url).status_code == 200, url


def test_bajo_rendimiento_del_docente_se_limita_a_sus_cursos(esc):
    c = cli(esc['ajeno'])
    assert c.get('/api/reportes/bajo-rendimiento/', {'curso_id': esc['proyecto'].id_curso_id}).status_code == 403
    assert c.get('/api/reportes/bajo-rendimiento/', {'proyecto_id': esc['proyecto'].id}).status_code == 403
    sin_filtro = c.get('/api/reportes/bajo-rendimiento/', {'solo_riesgo': 'false'})
    assert sin_filtro.status_code == 200
    ids = [e['id'] for e in sin_filtro.json().get('estudiantes', sin_filtro.json())]
    assert esc['miembro'].id not in ids
    propio = cli(esc['dueno']).get('/api/reportes/bajo-rendimiento/', {'solo_riesgo': 'false'})
    assert esc['miembro'].id in [e['id'] for e in propio.json().get('estudiantes', propio.json())]


def test_docente_ajeno_no_exporta_reportes(esc):
    r = cli(esc['ajeno']).post('/api/exportar/reporte/', {
        'tipo_reporte': 'proyecto', 'formato': 'excel', 'parametros': {'proyecto_id': esc['proyecto'].id}}, format='json')
    assert r.status_code == 403


def test_lider_ve_su_propio_reporte_solo_en_su_proyecto(esc):
    lider = esc['miembro']
    lider.tipo_rol = 'lider_equipo'
    lider.save()
    ok = cli(lider).get(f"/api/reportes/estudiante/{lider.id}/proyecto/{esc['proyecto'].id}/")
    assert ok.status_code == 200
    ajeno = cli(lider).get(f"/api/reportes/estudiante/{lider.id}/proyecto/{esc['otro_proyecto'].id}/")
    assert ajeno.status_code == 403


# --- S-04..S-08: evaluación ---------------------------------------------------

def test_docente_ajeno_no_lee_evaluaciones_de_otro_curso(esc):
    c = cli(esc['ajeno'])
    pid, eid = esc['proyecto'].id, esc['miembro'].id
    assert c.get(f'/api/proyectos/{pid}/autoevaluaciones/mia/', {'estudiante_id': eid}).status_code == 403
    assert c.get(f'/api/proyectos/{pid}/coevaluaciones/promedio/').status_code == 403
    assert c.get(f'/api/usuarios/{eid}/retroalimentaciones/').status_code == 403
    d = cli(esc['dueno'])
    assert d.get(f'/api/proyectos/{pid}/coevaluaciones/promedio/').status_code == 200
    assert d.get(f'/api/usuarios/{eid}/retroalimentaciones/').status_code == 200


def test_rubricas_de_un_proyecto(esc):
    url = f"/api/proyectos/{esc['proyecto'].id}/rubricas/"
    assert cli(esc['estudiante_ajeno']).get(url).status_code == 403
    assert cli(esc['docente_ajeno'] if 'docente_ajeno' in esc else esc['ajeno']).get(url).status_code == 403
    assert cli(esc['miembro']).get(url).status_code == 200
    assert cli(esc['dueno']).get(url).status_code == 200
    cuerpo = {'nombre': 'R', 'descripcion': 'd', 'tipo': 'general', 'peso_total': 100,
              'criterios': [{'nombre': 'C', 'descripcion': 'c', 'peso_porcentual': 100, 'niveles': [
                  {'nivel': 1, 'descripcion': 'n', 'puntos': 3}]}]}
    assert cli(esc['ajeno']).post(url, cuerpo, format='json').status_code == 403


def test_no_se_crea_rubrica_en_proyecto_ajeno(esc):
    cuerpo = {'nombre': 'R', 'descripcion': 'd', 'tipo': 'general', 'peso_total': 100,
              'id_proyecto': esc['proyecto'].id,
              'criterios': [{'nombre': 'C', 'descripcion': 'c', 'peso_porcentual': 100, 'niveles': [
                  {'nivel': 1, 'descripcion': 'n', 'puntos': 3}]}]}
    r = cli(esc['ajeno']).post('/api/rubricas/', cuerpo, format='json')
    assert r.status_code == 400, r.content
    assert not Rubrica.objects.filter(id_proyecto=esc['proyecto']).exists()


def test_retroalimentacion_no_acepta_recursos_de_otro_proyecto(esc):
    url = f"/api/proyectos/{esc['proyecto'].id}/retroalimentaciones/"
    equipo_ajeno = EquipoFactory(proyecto=esc['otro_proyecto'], cupo_maximo=3)
    r = cli(esc['dueno']).post(url, {'tipo': 'grupal', 'contenido': 'x', 'id_equipo': equipo_ajeno.id}, format='json')
    assert r.status_code == 400, r.content
    r = cli(esc['dueno']).post(url, {'tipo': 'individual', 'contenido': 'x', 'id_estudiante': esc['estudiante_ajeno'].id}, format='json')
    assert r.status_code == 400, r.content
    r = cli(esc['dueno']).post(url, {'tipo': 'grupal', 'contenido': 'x', 'id_equipo': esc['equipo'].id}, format='json')
    assert r.status_code == 201, r.content


def test_rubrica_de_otro_proyecto_no_sirve_para_evaluar_ni_coevaluar(esc):
    from apps.evaluacion.serializers import EvaluacionCreateSerializer
    rubrica_ajena = Rubrica.objects.create(
        nombre='R', descripcion='d', tipo='general', peso_total=100,
        id_proyecto=esc['otro_proyecto'], id_docente=esc['ajeno'])
    from apps.evaluacion.models import CriterioRubrica, NivelDesempeno
    criterio = CriterioRubrica.objects.create(id_rubrica=rubrica_ajena, nombre='C', peso_porcentual=100)
    nivel = NivelDesempeno.objects.create(id_criterio=criterio, nivel=1, etiqueta='insuficiente', puntos=1)
    s = EvaluacionCreateSerializer(
        data={'id_rubrica': rubrica_ajena.id,
              'calificaciones': [{'id_criterio': criterio.id, 'id_nivel_seleccionado': nivel.id}]},
        context={'request': type('R', (), {'user': esc['dueno']})(), 'entregable': esc['ent']})
    assert not s.is_valid()
    assert 'id_rubrica' in str(s.errors)


# --- S-11 / S-12 -------------------------------------------------------------

def test_raps_solo_para_participantes(esc):
    url = f"/api/proyectos/{esc['proyecto'].id}/raps/"
    assert cli(esc['estudiante_ajeno']).get(url).status_code == 403
    assert cli(esc['ajeno']).get(url).status_code == 403
    assert cli(esc['miembro']).get(url).status_code == 200
    assert cli(esc['dueno']).get(url).status_code == 200


def test_actividad_no_acepta_equipo_de_otro_proyecto(esc):
    from apps.cursos.serializers import ActividadCreateSerializer
    equipo_ajeno = EquipoFactory(proyecto=esc['otro_proyecto'], cupo_maximo=3)
    s = ActividadCreateSerializer(
        data={'nombre': 'N', 'fecha_limite': '2026-03-10', 'prioridad': 'media', 'estado': 'pendiente',
              'id_equipo_asignado': equipo_ajeno.id},
        context={'fase': esc['fase']})
    assert not s.is_valid()
    assert 'id_equipo_asignado' in s.errors


# --- A-12 / A-13: archivos subidos ---------------------------------------------------

def _subir(cliente_, entregable, nombre, contenido, tipo):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return cliente_.post(f"/api/entregables/{entregable.id}/archivos/",
                         {'archivo': SimpleUploadedFile(nombre, contenido, content_type=tipo)}, format='multipart')


@pytest.mark.parametrize('nombre,contenido,tipo,codigo', [
    ('a.pdf', b'%PDF-1.4 ok', 'application/pdf', 201),
    ('a.png', b'\x89PNG\r\n\x1a\nxxxx', 'image/png', 201),
    ('a.png', b'<html><script>alert(1)</script>', 'image/png', 400),   # html renombrado a png
    ('a.pdf', b'MZ\x90\x00 ejecutable', 'application/pdf', 400),
    ('a.html', b'<html></html>', 'text/html', 400),
    ('a.svg', b'<svg onload=alert(1)>', 'image/svg+xml', 400),
])
def test_adjuntos_se_validan_por_contenido(esc, nombre, contenido, tipo, codigo):
    ent = Entregable.objects.create(id_actividad=esc['act'], id_equipo=esc['equipo'], titulo='B', descripcion='d',
                                    tipo='documento', estado='borrador')
    r = _subir(cli(esc['miembro']), ent, nombre, contenido, tipo)
    assert r.status_code == codigo, r.content
    if codigo == 201:
        assert 'ruta' not in r.json() and 'nombre_almacenado' not in r.json()


def test_el_parametro_de_formatos_no_permite_html_ni_svg(esc):
    ParametroSistema.objects.update_or_create(
        clave='formatos_archivo_permitidos',
        defaults={'valor': 'pdf,html,svg,js', 'categoria': 'archivos', 'tipo_dato': 'string'})
    ent = Entregable.objects.create(id_actividad=esc['act'], id_equipo=esc['equipo'], titulo='B', descripcion='d',
                                    tipo='documento', estado='borrador')
    assert _subir(cli(esc['miembro']), ent, 'a.html', b'<html></html>', 'text/html').status_code == 400


def _foto(cliente_, contenido, tipo='image/png', nombre='f.png'):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return cliente_.post('/api/usuarios/foto-perfil/', {'foto': SimpleUploadedFile(nombre, contenido, content_type=tipo)},
                         format='multipart')


def test_foto_de_perfil_se_valida_por_contenido(esc, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    c = cli(esc['miembro'])
    assert _foto(c, b'<html><script>alert(1)</script>').status_code == 400
    ok = _foto(c, b'\x89PNG\r\n\x1a\n' + b'0' * 20)
    assert ok.status_code == 200, ok.content
    assert ok.json()['foto_perfil'].endswith('.png')


def test_cambiar_foto_no_borra_archivos_fuera_de_la_carpeta(esc, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / 'media'
    (tmp_path / 'media').mkdir()
    victima = tmp_path / 'importante.txt'
    victima.write_text('no me borres')
    # aunque la BD tuviera una ruta manipulada, la subida no debe salir de fotos_perfil/
    Usuario = type(esc['miembro'])
    Usuario.objects.filter(pk=esc['miembro'].pk).update(foto_perfil='/media/fotos_perfil/../../importante.txt')
    assert _foto(cli(Usuario.objects.get(pk=esc['miembro'].pk)), b'\x89PNG\r\n\x1a\n' + b'0' * 20).status_code == 200
    assert victima.exists()


# --- A-08: cargas masivas de Excel --------------------------------------------------

def _xlsx(filas):
    import io as _io
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    for f in filas:
        ws.append(f)
    b = _io.BytesIO()
    wb.save(b)
    b.seek(0)
    return b


def test_carga_masiva_rechaza_archivos_con_demasiadas_filas(esc):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.usuarios.excel_seguro import MAX_FILAS
    contenido = _xlsx([['Codigo', 'Nombre']] + [[str(i), 'x'] for i in range(MAX_FILAS + 5)]).read()
    r = cli(esc['admin']).post('/api/usuarios/carga-masiva/',
                               {'archivo': SimpleUploadedFile('a.xlsx', contenido)}, format='multipart')
    assert r.status_code == 400 and 'filas' in r.json()['detail']


def test_carga_masiva_rechaza_archivos_que_no_son_xlsx_o_son_enormes(esc):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.usuarios.excel_seguro import MAX_BYTES
    falso = cli(esc['admin']).post('/api/usuarios/carga-masiva/',
                                   {'archivo': SimpleUploadedFile('a.xlsx', b'esto no es un zip')}, format='multipart')
    assert falso.status_code == 400
    grande = cli(esc['admin']).post('/api/usuarios/carga-masiva/',
                                    {'archivo': SimpleUploadedFile('a.xlsx', b'0' * (MAX_BYTES + 1))}, format='multipart')
    assert grande.status_code == 400 and '2 MB' in grande.json()['detail']
