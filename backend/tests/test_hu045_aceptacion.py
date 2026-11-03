"""
HU-045 — SCRUM-575: Prueba de aceptación de la búsqueda global.

Escenario de la tarjeta: como director, buscar un estudiante por código y
llegar a su detalle en menos de 3 s; como docente, no tiene búsqueda global.

Nota de alcance: la tarjeta pide frontend/cypress/e2e/hu045-busqueda.cy.js,
pero la barra de búsqueda global (SCRUM-572 y SCRUM-573, de Ovallos) todavía
no está en develop ni en ninguna rama remota. Por eso esta prueba recorre el
flujo sobre la API con las mismas llamadas que hará la interfaz: búsqueda →
enlace del resultado → detalle del estudiante. La verificación visual queda
pendiente para cuando SCRUM-573 esté en develop.

Hallazgo para SCRUM-573: el enlace de un usuario para el director es
/director/riesgo?estudiante_id=<id>, pero EstudiantesRiesgoDirector.jsx no lee
ese parámetro, así que hoy no abriría el detalle del estudiante (HAL-045-01).

Hallazgo HAL-045-02 (HU-032, fuera del alcance de HU-045): sin curso_id ni
proyecto_id, GET /api/reportes/estudiantes/:id/rendimiento/ calcula el promedio
del grupo con una llamada a calcular_rendimiento_estudiante() por cada
estudiante activo (_calcular_promedio_grupo). Con 1.000 estudiantes la
petición pasó de 10 minutos en la BD de prueba. Se documenta con un xfail.
"""
import time
from urllib.parse import parse_qs, urlparse

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.usuarios.models import Usuario
from tests.factories import (CursoFactory, DocenteFactory, EquipoFactory, MiembroEquipoFactory, ProyectoFactory,
                             UsuarioFactory)


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def mil_usuarios(db):
    Usuario.objects.bulk_create([
        Usuario(nombre=f'Estudiante{i}', apellido='Carga', codigo=f'115{i:04d}',
                correo=f'carga{i}@ufps.edu.co', tipo_rol=Usuario.TipoRol.ESTUDIANTE, password='x')
        for i in range(1000)
    ])


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


@pytest.mark.django_db
def test_ca01_director_busca_estudiante_por_codigo_y_llega_a_su_detalle_en_menos_de_3_s(mil_usuarios):
    estudiante = UsuarioFactory(nombre='Valentina', apellido='Suárez', codigo='1152044')
    proyecto = ProyectoFactory()
    MiembroEquipoFactory(equipo=EquipoFactory(proyecto=proyecto), usuario=estudiante)
    director = _cliente(UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR))

    inicio = time.perf_counter()
    resp = director.get('/api/busqueda/', {'q': '1152044'})
    t_busqueda = time.perf_counter() - inicio
    assert resp.status_code == 200
    assert len(resp.data['usuarios']) == 1
    resultado = resp.data['usuarios'][0]
    assert resultado['titulo'] == 'Valentina Suárez'

    # El enlace del resultado identifica al estudiante para abrir su detalle
    enlace = urlparse(resultado['enlace'])
    assert enlace.path == '/director/riesgo'
    estudiante_id = int(parse_qs(enlace.query)['estudiante_id'][0])
    assert estudiante_id == estudiante.pk

    # Detalle del estudiante filtrado por su proyecto (como PerfilRendimientoEstudiante.jsx)
    detalle = director.get(f'/api/reportes/estudiantes/{estudiante_id}/rendimiento/',
                           {'proyecto_id': proyecto.pk})
    duracion = time.perf_counter() - inicio
    print(f'\nHU-045 búsqueda {t_busqueda:.3f} s; búsqueda + detalle {duracion:.3f} s (1000 usuarios)')

    assert detalle.status_code == 200
    assert detalle.data['estudiante']['codigo'] == '1152044'
    assert detalle.data['estudiante']['correo'] == estudiante.correo
    assert duracion < 3


@pytest.mark.django_db
def test_ca02_director_busca_proyecto_y_abre_su_reporte():
    curso = CursoFactory(nombre='Ingeniería de Software II', codigo='IS2-01')
    proyecto = ProyectoFactory(id_curso=curso, nombre='App de tutorías')
    director = _cliente(UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR))

    resp = director.get('/api/busqueda/', {'q': 'tutorías'})
    assert resp.status_code == 200
    item = resp.data['proyectos'][0]
    assert item['subtitulo'] == 'Ingeniería de Software II'
    assert item['enlace'] == f'/director/reportes/proyecto/{proyecto.pk}'

    reporte = director.get(f'/api/reportes/proyecto/{proyecto.pk}/')
    assert reporte.status_code == 200


@pytest.mark.django_db
def test_ca03_docente_no_tiene_busqueda_global():
    UsuarioFactory(codigo='1152044')
    resp = _cliente(DocenteFactory()).get('/api/busqueda/', {'q': '1152044'})
    assert resp.status_code == 403
    assert 'usuarios' not in resp.data


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason='HAL-045-02: _calcular_promedio_grupo hace consultas por cada estudiante')
def test_ca04_detalle_sin_filtros_no_crece_con_el_numero_de_estudiantes():
    """Las consultas del detalle no deberían depender de cuántos estudiantes hay en el sistema."""
    estudiante = UsuarioFactory(codigo='1152044')
    director = _cliente(UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR))
    url = f'/api/reportes/estudiantes/{estudiante.pk}/rendimiento/'

    UsuarioFactory.create_batch(2)
    with CaptureQueriesContext(connection) as pocos:
        assert director.get(url).status_code == 200
    UsuarioFactory.create_batch(20)
    with CaptureQueriesContext(connection) as muchos:
        assert director.get(url).status_code == 200

    print(f'\nHU-045 consultas del detalle: 3 estudiantes={len(pocos)}, 23 estudiantes={len(muchos)}')
    assert len(muchos) == len(pocos)
