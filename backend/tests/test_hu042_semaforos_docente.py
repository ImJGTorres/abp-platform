"""
HU-042 — Panel de semáforos de proyectos del docente (SCRUM-552) y filtro por color (SCRUM-553).
"""
import time

import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad, Proyecto
from apps.reportes.semaforo import semaforos_docente
from tests.factories import (ActividadFactory, CursoFactory, DocenteFactory, EquipoFactory,
                             FaseProyectoFactory, MiembroEquipoFactory, ProyectoFactory, UsuarioFactory)

URL = '/api/reportes/semaforos/docente/'

# Las vistas reales se crean con migraciones de PostgreSQL (cursos 0019 y 0024). Con SQLite y
# --nomigrations no existen: se crean aquí versiones equivalentes, sin la sintaxis '::numeric'.
VISTAS_SQLITE = [
    """
    CREATE VIEW IF NOT EXISTS vista_progreso_proyecto AS
    SELECT p.id AS id_proyecto, p.nombre AS nombre_proyecto, p.estado AS estado_proyecto,
           COUNT(DISTINCT fp.id) AS total_fases,
           COUNT(DISTINCT CASE WHEN fp.estado = 'completada' THEN fp.id END) AS fases_completadas,
           COUNT(DISTINCT CASE WHEN fp.estado = 'en_progreso' THEN fp.id END) AS fases_en_progreso,
           COALESCE(ROUND(AVG(fp.porcentaje_completado)), 0) AS porcentaje_progreso,
           COUNT(DISTINCT a.id) AS total_actividades,
           COUNT(DISTINCT CASE WHEN a.estado = 'completada' THEN a.id END) AS actividades_completadas
    FROM proyecto p
    LEFT JOIN fase_proyecto fp ON fp.id_proyecto_id = p.id
    LEFT JOIN actividad a ON a.id_fase_id = fp.id
    GROUP BY p.id, p.nombre, p.estado
    """,
    """
    CREATE VIEW IF NOT EXISTS vista_avance_estudiante_proyecto AS
    SELECT em.usuario_id, ee.proyecto_id,
           ROUND(AVG(av.porcentaje_completado), 2) AS promedio_avance_pct,
           ROUND(AVG(av.porcentaje_completado) / 100.0 * 5, 2) AS nota_promedio_5,
           COUNT(DISTINCT av.id_actividad_id) AS actividades_con_avance
    FROM avance_actividad av
    JOIN actividad a ON a.id = av.id_actividad_id
    JOIN equipos_equipo ee ON ee.id = a.id_equipo_asignado_id
    JOIN equipos_miembroequipo em ON em.equipo_id = ee.id AND em.estado = 'activo'
    WHERE av.id_usuario_id = em.usuario_id
    GROUP BY em.usuario_id, ee.proyecto_id
    """,
]


@pytest.fixture(autouse=True)
def entorno_bd(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})
    if connection.vendor == 'sqlite':
        with connection.cursor() as cur:
            for sql in VISTAS_SQLITE:
                cur.execute(sql)


def _proyecto(docente, nombre, porcentaje_fase, avances, completadas, pendientes, estado=None):
    """
    Proyecto del docente con una fase al `porcentaje_fase`, un equipo de un estudiante,
    `completadas` actividades completadas y `pendientes` pendientes; el estudiante registra
    un avance de cada valor de `avances` sobre las completadas.
    """
    curso = CursoFactory(id_docente=docente, nombre=f'Curso {nombre}')
    proyecto = ProyectoFactory(id_curso=curso, nombre=nombre,
                               **({'estado': estado} if estado else {}))
    fase = FaseProyectoFactory(id_proyecto=proyecto, porcentaje_completado=porcentaje_fase)
    equipo = EquipoFactory(proyecto=proyecto)
    est = UsuarioFactory()
    MiembroEquipoFactory(equipo=equipo, usuario=est)
    hechas = [ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, estado=Actividad.Estado.COMPLETADA)
              for _ in range(completadas)]
    for _ in range(pendientes):
        ActividadFactory(id_fase=fase, id_equipo_asignado=equipo)
    for act, pct in zip(hechas, avances):
        AvanceActividad.objects.create(id_actividad=act, id_usuario=est, descripcion='a',
                                       porcentaje_completado=pct)
    return proyecto


def _get(usuario, **params):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c.get(URL, params)


@pytest.fixture
def docente_con_3_proyectos():
    docente = DocenteFactory()
    verde = _proyecto(docente, 'A-Verde', 80, avances=[100, 100], completadas=2, pendientes=0)
    amarillo = _proyecto(docente, 'B-Amarillo', 50, avances=[64], completadas=1, pendientes=0)  # nota 3.2
    rojo = _proyecto(docente, 'C-Rojo', 20, avances=[100], completadas=1, pendientes=1)         # 50 % incumplidas
    return docente, {'verde': verde, 'amarillo': amarillo, 'rojo': rojo}


# ── SCRUM-552 ────────────────────────────────────────────────────────────────

def test_docente_con_3_proyectos_recibe_3_elementos_con_nivel_y_avance(docente_con_3_proyectos):
    docente, proyectos = docente_con_3_proyectos

    inicio = time.perf_counter()
    r = _get(docente)
    duracion = time.perf_counter() - inicio

    assert r.status_code == 200
    assert duracion < 1
    assert [(e['nombre'], e['nivel']) for e in r.data] == [
        ('A-Verde', 'verde'), ('B-Amarillo', 'amarillo'), ('C-Rojo', 'rojo')]
    assert r.data[0] == {
        'proyecto_id': proyectos['verde'].id,
        'nombre': 'A-Verde',
        'curso_id': proyectos['verde'].id_curso_id,
        'curso_nombre': 'Curso A-Verde',
        'nivel': 'verde',
        'porcentaje_avance': 80,
    }


def test_consultas_constantes_sin_ciclo_por_estudiante(docente_con_3_proyectos):
    from django.test.utils import CaptureQueriesContext

    docente, _ = docente_con_3_proyectos
    with CaptureQueriesContext(connection) as con_3:
        assert len(semaforos_docente(docente.id)) == 3

    for nombre in ('D-Extra', 'E-Extra'):
        _proyecto(docente, nombre, 10, avances=[100, 90, 80], completadas=3, pendientes=2)
    with CaptureQueriesContext(connection) as con_5:
        assert len(semaforos_docente(docente.id)) == 5

    # proyectos + VistaProgresoProyecto + notas agrupadas + 4 parámetros de umbral
    assert len(con_3.captured_queries) == len(con_5.captured_queries) == 7


def test_excluye_finalizados_y_proyectos_de_otros_docentes(docente_con_3_proyectos):
    docente, _ = docente_con_3_proyectos
    _proyecto(docente, 'Z-Finalizado', 100, avances=[100], completadas=1, pendientes=0,
              estado=Proyecto.Estado.FINALIZADO)
    _proyecto(DocenteFactory(), 'Ajeno', 50, avances=[100], completadas=1, pendientes=0)

    nombres = [e['nombre'] for e in _get(docente).data]

    assert nombres == ['A-Verde', 'B-Amarillo', 'C-Rojo']


def test_docente_sin_proyectos_recibe_lista_vacia():
    r = _get(DocenteFactory())
    assert r.status_code == 200 and r.data == []


def test_proyecto_sin_actividades_es_verde():
    docente = DocenteFactory()
    ProyectoFactory(id_curso=CursoFactory(id_docente=docente))
    assert [e['nivel'] for e in _get(docente).data] == ['verde']


@pytest.mark.parametrize('rol', ['estudiante', 'lider_equipo', 'director', 'administrador'])
def test_otros_roles_reciben_403(rol):
    assert _get(UsuarioFactory(tipo_rol=rol)).status_code == 403


def test_sin_autenticar_retorna_401():
    assert APIClient().get(URL).status_code == 401


def test_nivel_usa_los_umbrales_de_configuracion(docente_con_3_proyectos):
    docente, _ = docente_con_3_proyectos
    ParametroSistema.objects.create(clave='umbral_nota_alerta', valor='3.0',
                                    categoria='general', tipo_dato='string')

    niveles = {e['nombre']: e['nivel'] for e in _get(docente).data}

    assert niveles['B-Amarillo'] == 'verde'  # 3.2 ya no está por debajo del umbral de alerta


# ── SCRUM-553 ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('color, esperado', [
    ('rojo', ['C-Rojo']),
    ('amarillo', ['B-Amarillo']),
    ('verde', ['A-Verde']),
])
def test_filtro_por_color_coincide_con_el_nivel_sin_filtro(docente_con_3_proyectos, color, esperado):
    docente, _ = docente_con_3_proyectos
    sin_filtro = _get(docente).data

    r = _get(docente, color=color)

    assert r.status_code == 200
    assert [e['nombre'] for e in r.data] == esperado
    assert r.data == [e for e in sin_filtro if e['nivel'] == color]


def test_color_invalido_retorna_400():
    r = _get(DocenteFactory(), color='azul')
    assert r.status_code == 400
    assert 'verde, amarillo, rojo' in r.data['error']
