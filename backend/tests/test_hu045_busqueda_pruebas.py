"""
HU-045 — SCRUM-574: Pruebas unitarias del backend de la búsqueda global.

GET /api/busqueda/?q= (SCRUM-570, buscar_global() en apps/reportes/busqueda.py)
con índices varchar_pattern_ops (SCRUM-571).

Complementa a tests/test_hu045_busqueda.py (pruebas de desarrollo de Gabriel):
aquí se prueban los criterios de la tarjeta de SCRUM-574 (resultados
clasificados por tipo, docente → 403, q de 1 carácter → 400, tiempo < 3 s con
el fixture de 1.000 usuarios) y sus bordes: campos de búsqueda por tipo,
enlaces por rol, límite y orden, entradas raras y existencia de los índices.
"""
import time

import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Curso, Proyecto
from apps.entregables.models import Entregable
from apps.reportes.busqueda import LIMITE_POR_TIPO, MIN_CARACTERES, buscar_global
from apps.usuarios.models import Usuario
from tests.factories import (ActividadFactory, AdminFactory, CursoFactory, EquipoFactory, FaseProyectoFactory,
                             ProyectoFactory, UsuarioFactory)

URL = '/api/busqueda/'
TIPOS = {'cursos', 'proyectos', 'usuarios', 'entregables'}


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


def _cliente(usuario=None):
    c = APIClient()
    if usuario is not None:
        c.force_authenticate(user=usuario)
    return c


def _director():
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)


def _buscar(q, usuario=None):
    return _cliente(usuario or _director()).get(URL, {'q': q})


def _ids(resp, tipo):
    return [r['id'] for r in resp.data[tipo]]


def _entregable(proyecto, titulo):
    fase = FaseProyectoFactory(id_proyecto=proyecto)
    return Entregable.objects.create(id_actividad=ActividadFactory(id_fase=fase),
                                     id_equipo=EquipoFactory(proyecto=proyecto),
                                     titulo=titulo, descripcion='-', tipo='documento')


@pytest.fixture
def datos(db):
    """Un registro de cada tipo con palabras distintas para comprobar la clasificación."""
    curso = CursoFactory(nombre='Arquitectura de Software', codigo='ARQ-777')
    proyecto = ProyectoFactory(id_curso=curso, nombre='Sistema Marítimo')
    entregable = _entregable(proyecto, 'Informe de arranque')
    estudiante = UsuarioFactory(nombre='Zoraida', apellido='Arciniegas', codigo='1151999',
                                correo='zoraida.arciniegas@ufps.edu.co')
    return curso, proyecto, entregable, estudiante


@pytest.fixture
def mil_usuarios(db):
    """Fixture de 1.000 usuarios que piden la tarjeta y el criterio de rendimiento."""
    Usuario.objects.bulk_create([
        Usuario(nombre=f'Estudiante{i}', apellido='Carga', codigo=f'115{i:04d}',
                correo=f'carga{i}@ufps.edu.co', tipo_rol=Usuario.TipoRol.ESTUDIANTE, password='x')
        for i in range(1000)
    ])


# ── Clasificación por tipo ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_respuesta_clasificada_en_los_cuatro_tipos_con_formato_de_item(datos):
    resp = _buscar('ar')  # Arquitectura, Marítimo, arranque, Arciniegas
    assert resp.status_code == 200
    assert set(resp.data) == TIPOS
    for tipo in TIPOS:
        assert resp.data[tipo], tipo
        for item in resp.data[tipo]:
            assert set(item) == {'id', 'titulo', 'subtitulo', 'enlace'}


@pytest.mark.django_db
@pytest.mark.parametrize('q, tipo', [('arquitectura', 'cursos'), ('marítimo', 'proyectos'),
                                     ('arranque', 'entregables'), ('zoraida', 'usuarios')])
def test_cada_termino_cae_solo_en_su_tipo(datos, q, tipo):
    resp = _buscar(q)
    assert resp.status_code == 200
    assert len(resp.data[tipo]) == 1
    assert all(resp.data[t] == [] for t in TIPOS - {tipo})


@pytest.mark.django_db
def test_sin_coincidencias_200_con_listas_vacias(datos):
    resp = _buscar('xyzxyz')
    assert resp.status_code == 200
    assert resp.data == {t: [] for t in TIPOS}


@pytest.mark.django_db
def test_busqueda_no_distingue_mayusculas(datos):
    curso = datos[0]
    assert _ids(_buscar('ARQUITECTURA'), 'cursos') == [curso.pk]
    assert _ids(_buscar('arq-777'), 'cursos') == [curso.pk]


# ── Campos por los que busca cada tipo ───────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('q', ['1151999', 'Arciniegas', 'zoraida.arciniegas@ufps'])
def test_usuario_por_codigo_apellido_y_correo(datos, q):
    estudiante = datos[3]
    resp = _buscar(q)
    assert _ids(resp, 'usuarios') == [estudiante.pk]
    item = resp.data['usuarios'][0]
    assert item['titulo'] == 'Zoraida Arciniegas'
    assert item['subtitulo'] == 'zoraida.arciniegas@ufps.edu.co · estudiante'


@pytest.mark.django_db
def test_curso_por_codigo_y_proyecto_con_nombre_del_curso(datos):
    curso, proyecto, _, _ = datos
    resp = _buscar('ARQ-7')
    assert resp.data['cursos'][0]['subtitulo'] == 'ARQ-777'
    resp = _buscar('marítimo')
    assert resp.data['proyectos'][0] == {'id': proyecto.pk, 'titulo': 'Sistema Marítimo',
                                         'subtitulo': 'Arquitectura de Software',
                                         'enlace': f'/director/reportes/proyecto/{proyecto.pk}'}


@pytest.mark.django_db
def test_entregable_enlaza_al_reporte_de_su_proyecto(datos):
    _, proyecto, entregable, _ = datos
    item = _buscar('arranque').data['entregables'][0]
    assert item == {'id': entregable.pk, 'titulo': 'Informe de arranque', 'subtitulo': 'Sistema Marítimo',
                    'enlace': f'/director/reportes/proyecto/{proyecto.pk}'}


# ── Enlaces según el rol ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_enlaces_de_director(datos):
    curso, _, _, estudiante = datos
    assert _buscar('arquitectura').data['cursos'][0]['enlace'] == f'/director/reportes?curso_id={curso.pk}'
    assert _buscar('1151999').data['usuarios'][0]['enlace'] == f'/director/riesgo?estudiante_id={estudiante.pk}'


@pytest.mark.django_db
def test_enlaces_de_administrador(datos):
    curso, _, _, estudiante = datos
    admin = AdminFactory()
    assert _buscar('arquitectura', admin).data['cursos'][0]['enlace'] == f'/admin/cursos/{curso.pk}'
    assert _buscar('1151999', admin).data['usuarios'][0]['enlace'] == f'/admin/registro?usuario_id={estudiante.pk}'


# ── Límite y orden ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_maximo_10_por_tipo_en_cursos_proyectos_y_entregables():
    curso = CursoFactory(nombre='Curso Límite 00', codigo='LIM-00')
    for i in range(1, 12):
        CursoFactory(nombre=f'Curso Límite {i:02d}', codigo=f'LIM-{i:02d}')
    proyectos = [ProyectoFactory(id_curso=curso, nombre=f'Límite proyecto {i:02d}') for i in range(12)]
    for i in range(12):
        _entregable(proyectos[0], f'Límite entregable {i:02d}')

    resp = _buscar('límite')

    assert LIMITE_POR_TIPO == 10
    assert len(resp.data['cursos']) == 10
    assert len(resp.data['proyectos']) == 10
    assert len(resp.data['entregables']) == 10


@pytest.mark.django_db
def test_resultados_ordenados_alfabeticamente():
    for nombre in ['Gamma', 'Alfa', 'Beta']:
        UsuarioFactory(nombre=nombre, apellido='Ordenado')
    resp = _buscar('ordenado')
    assert [u['titulo'] for u in resp.data['usuarios']] == ['Alfa Ordenado', 'Beta Ordenado', 'Gamma Ordenado']


# ── Validación del término ───────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('q', ['a', 'ñ', '  b  ', ''])
def test_q_de_menos_de_2_caracteres_400_con_mensaje(q):
    resp = _buscar(q)
    assert resp.status_code == 400
    assert f'al menos {MIN_CARACTERES} caracteres' in resp.data['error']


@pytest.mark.django_db
def test_sin_parametro_q_400():
    assert _cliente(_director()).get(URL).status_code == 400


@pytest.mark.django_db
def test_q_con_espacios_alrededor_se_recorta(datos):
    curso = datos[0]
    resp = _buscar('   arq-777   ')
    assert resp.status_code == 200
    assert _ids(resp, 'cursos') == [curso.pk]


@pytest.mark.django_db
@pytest.mark.parametrize('q', ['%%', '__', "' OR 1=1 --"])
def test_comodines_y_texto_malicioso_no_devuelven_todo(datos, q):
    resp = _buscar(q)
    assert resp.status_code == 200
    assert resp.data == {t: [] for t in TIPOS}


# ── Permisos ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('rol', [Usuario.TipoRol.DOCENTE, Usuario.TipoRol.ESTUDIANTE, Usuario.TipoRol.LIDER_EQUIPO])
def test_roles_sin_permiso_403(datos, rol):
    resp = _buscar('arquitectura', UsuarioFactory(tipo_rol=rol))
    assert resp.status_code == 403
    assert 'director o el administrador' in resp.data['error']


@pytest.mark.django_db
def test_rol_sin_permiso_recibe_403_aunque_q_sea_invalido():
    assert _buscar('a', UsuarioFactory(tipo_rol=Usuario.TipoRol.DOCENTE)).status_code == 403


@pytest.mark.django_db
def test_sin_autenticacion_401():
    assert _cliente().get(URL, {'q': 'arquitectura'}).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize('rol', [Usuario.TipoRol.DIRECTOR, Usuario.TipoRol.ADMINISTRADOR])
def test_director_y_admin_200(datos, rol):
    assert _buscar('arquitectura', UsuarioFactory(tipo_rol=rol)).status_code == 200


# ── Rendimiento e índices (SCRUM-571) ────────────────────────────────────────

@pytest.mark.django_db
def test_menos_de_3_segundos_con_1000_usuarios(mil_usuarios, datos):
    cliente = _cliente(_director())
    for q in ['estudiante', '1150500', 'zoraida']:
        inicio = time.perf_counter()
        resp = cliente.get(URL, {'q': q})
        duracion = time.perf_counter() - inicio
        print(f'\nHU-045 q={q!r} con 1000 usuarios: {duracion:.3f} s')
        assert resp.status_code == 200
        assert duracion < 3
    assert Usuario.objects.count() >= 1000


@pytest.mark.django_db
def test_con_1000_usuarios_codigo_exacto_trae_un_solo_estudiante(mil_usuarios):
    resp = _buscar('1150500')
    assert [u['titulo'] for u in resp.data['usuarios']] == ['Estudiante500 Carga']
    assert len(_buscar('estudiante').data['usuarios']) == 10


@pytest.mark.django_db
@pytest.mark.parametrize('modelo, indices', [
    (Usuario, {'idx_usuario_nombre', 'idx_usuario_apellido', 'idx_usuario_codigo'}),
    (Curso, {'idx_curso_nombre', 'idx_curso_codigo'}),
    (Proyecto, {'idx_proyecto_nombre'}),
    (Entregable, {'idx_entregable_titulo'}),
])
def test_indices_de_busqueda_existen_en_la_bd(modelo, indices):
    with connection.cursor() as cursor:
        existentes = set(connection.introspection.get_constraints(cursor, modelo._meta.db_table))
    assert indices <= existentes


@pytest.mark.django_db
def test_servicio_buscar_global_directo(datos):
    curso, proyecto, entregable, estudiante = datos
    r = buscar_global('ar', 'director')
    assert curso.pk in [c['id'] for c in r['cursos']]
    assert proyecto.pk in [p['id'] for p in r['proyectos']]
    assert entregable.pk in [e['id'] for e in r['entregables']]
    assert estudiante.pk in [u['id'] for u in r['usuarios']]
