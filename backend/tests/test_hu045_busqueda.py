"""
HU-045 — Búsqueda global GET /api/busqueda/?q= (SCRUM-570) con índices (SCRUM-571).
"""
import time

import pytest
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.entregables.models import Entregable
from apps.usuarios.models import Usuario
from tests.factories import (ActividadFactory, AdminFactory, CursoFactory, DocenteFactory, EquipoFactory,
                             FaseProyectoFactory, ProyectoFactory, UsuarioFactory)

URL = '/api/busqueda/'


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _director():
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)


@pytest.fixture
def datos(db):
    curso = CursoFactory(nombre='Ingeniería de Software', codigo='IS-901')
    proyecto = ProyectoFactory(id_curso=curso, nombre='Plataforma de ingreso')
    fase = FaseProyectoFactory(id_proyecto=proyecto)
    entregable = Entregable.objects.create(
        id_actividad=ActividadFactory(id_fase=fase), id_equipo=EquipoFactory(proyecto=proyecto),
        titulo='Informe de ingeniería', descripcion='-', tipo='documento')
    usuario = UsuarioFactory(nombre='Inguilda', apellido='Rojas')
    return curso, proyecto, entregable, usuario


@pytest.mark.django_db
def test_ing_devuelve_varios_tipos_agrupados(datos):
    curso, proyecto, entregable, usuario = datos
    resp = _cliente(_director()).get(URL, {'q': 'ing'})
    assert resp.status_code == 200
    assert set(resp.data) == {'cursos', 'proyectos', 'usuarios', 'entregables'}
    assert curso.pk in [c['id'] for c in resp.data['cursos']]
    assert proyecto.pk in [p['id'] for p in resp.data['proyectos']]
    assert usuario.pk in [u['id'] for u in resp.data['usuarios']]
    item = resp.data['entregables'][0]
    assert item == {'id': entregable.pk, 'titulo': 'Informe de ingeniería',
                    'subtitulo': 'Plataforma de ingreso',
                    'enlace': f'/director/reportes/proyecto/{proyecto.pk}'}


@pytest.mark.django_db
def test_busca_por_codigo_y_correo(datos):
    curso, _, _, usuario = datos
    resp = _cliente(AdminFactory()).get(URL, {'q': 'is-901'})
    assert [c['enlace'] for c in resp.data['cursos']] == [f'/admin/cursos/{curso.pk}']
    resp = _cliente(AdminFactory()).get(URL, {'q': usuario.correo})
    assert [u['id'] for u in resp.data['usuarios']] == [usuario.pk]


@pytest.mark.django_db
@pytest.mark.parametrize('factory', [DocenteFactory, UsuarioFactory])
def test_docente_y_estudiante_403(factory):
    assert _cliente(factory()).get(URL, {'q': 'ing'}).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('q', ['', 'a', ' i '])
def test_q_menor_a_2_caracteres_400(q):
    assert _cliente(_director()).get(URL, {'q': q}).status_code == 400


@pytest.mark.django_db
def test_maximo_10_por_tipo_y_menos_de_3_segundos_con_1000_usuarios():
    Usuario.objects.bulk_create([
        Usuario(nombre=f'Ingrid{i}', apellido='Test', correo=f'perf{i}@ufps.edu.co',
                tipo_rol=Usuario.TipoRol.ESTUDIANTE, password='x')
        for i in range(1000)
    ])
    cliente = _cliente(_director())
    inicio = time.perf_counter()
    resp = cliente.get(URL, {'q': 'ing'})
    duracion = time.perf_counter() - inicio
    print(f'\nHU-045 búsqueda con 1000 usuarios: {duracion:.3f} s')
    assert resp.status_code == 200
    assert len(resp.data['usuarios']) == 10
    assert duracion < 3
