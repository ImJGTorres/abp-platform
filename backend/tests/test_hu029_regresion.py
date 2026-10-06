"""
HU-029 — Pruebas de regresión del semáforo académico de 3 niveles (SCRUM-593).

Complementa test_hu029_semaforo.py (Nicole, regla con mocks) y
test_hu029_bajo_rendimiento.py (Gabriel, vista con mocks) con un escenario
real en BD llamado por URL:
  - bordes de clasificar_semaforo() con los umbrales leídos de ParametroSistema
    y bordes calculados desde avances reales;
  - GET /api/reportes/bajo-rendimiento/?nivel= (filtro, 400, 403, bitácora);
  - regresión de las vistas que consumían en_riesgo: EstudiantesRiesgo (docente),
    Riesgo (director), Perfil de rendimiento y el PDF del estudiante;
  - consultas SQL del filtro del director según el número de estudiantes
    (el "< 3 s" de la aceptación se mide a mano en la app desplegada).

Hallazgos marcados con xfail(strict=True):
  PRB-09 — bajo-rendimiento hace 6 consultas por estudiante (N+1).

Escenario (umbrales por defecto RF34), un curso con un proyecto:
  rojo (nota 0, 100 % incumplidas), amarillo (nota 5, 25 % incumplidas),
  verde (nota 5, 0 %), verde_sin_actividades.
"""
import time

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad, CursoEstudiante
from apps.reportes.semaforo import clasificar_semaforo
from tests.factories import (
    ActividadFactory, CursoFactory, DocenteFactory, EquipoFactory, FaseProyectoFactory,
    MiembroEquipoFactory, ProyectoFactory, UsuarioFactory,
)

URL = '/api/reportes/bajo-rendimiento/'
CAMPOS_ESTUDIANTE = {
    'id', 'nombre', 'apellido', 'correo', 'codigo', 'nota_promedio',
    'porcentaje_actividades_incumplidas', 'actividades_incumplidas', 'total_actividades',
    'entregables_rechazados', 'total_entregables', 'nivel_semaforo', 'en_riesgo', 'alertas',
}
UMBRALES_DEFECTO = [
    ('umbral_nota_bajo_rendimiento', '3.0', 'rendimiento', 'float'),
    ('umbral_porcentaje_actividades_incumplidas', '50', 'rendimiento', 'integer'),
    ('umbral_nota_alerta', '3.5', 'rendimiento', 'float'),
    ('umbral_porcentaje_alerta', '25', 'rendimiento', 'integer'),
    ('max_estudiantes_por_equipo', '10', 'general', 'integer'),
]


def _inscribir(curso, proyecto=None, completadas=0, pendientes=0, avance=0):
    """
    Estudiante inscrito en el curso. Con actividades, va en su propio equipo
    del proyecto. avance = porcentaje_completado de cada avance (nota = avance/100*5).
    """
    est = UsuarioFactory()
    CursoEstudiante.objects.create(curso=curso, estudiante=est)
    if completadas or pendientes:
        equipo = EquipoFactory(proyecto=proyecto)
        MiembroEquipoFactory(equipo=equipo, usuario=est)
        fase = FaseProyectoFactory(id_proyecto=proyecto)
        estados = [Actividad.Estado.COMPLETADA] * completadas + [Actividad.Estado.PENDIENTE] * pendientes
        for estado in estados:
            act = ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, estado=estado)
            AvanceActividad.objects.create(
                id_actividad=act, id_usuario=est, descripcion='avance', porcentaje_completado=avance,
            )
    return est


@pytest.fixture
def umbrales(db):
    """Umbrales RF34 por defecto, explícitos para no depender de los datos de la BD."""
    for clave, valor, categoria, tipo in UMBRALES_DEFECTO:
        ParametroSistema.objects.update_or_create(
            clave=clave, defaults={'valor': valor, 'categoria': categoria, 'tipo_dato': tipo})


@pytest.fixture
def escenario(umbrales):
    curso = CursoFactory()
    proyecto = ProyectoFactory(id_curso=curso)
    return {
        'curso': curso,
        'proyecto': proyecto,
        'rojo': _inscribir(curso, proyecto, completadas=0, pendientes=2, avance=0),
        'amarillo': _inscribir(curso, proyecto, completadas=3, pendientes=1, avance=100),
        'verde': _inscribir(curso, proyecto, completadas=2, pendientes=0, avance=100),
        'verde_sin_actividades': _inscribir(curso),
    }


def _cliente(usuario):
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def director():
    return _cliente(UsuarioFactory(tipo_rol='director'))


@pytest.fixture
def docente(escenario):
    return _cliente(escenario['curso'].id_docente)


# ── Bordes de clasificar_semaforo() con umbrales de ParametroSistema ───────

@pytest.mark.django_db
@pytest.mark.parametrize('nota,pct,esperado', [
    (2.9, 0, 'rojo'),
    (3.0, 0, 'amarillo'),
    (3.5, 0, 'verde'),
    (4.5, 25, 'amarillo'),
    (4.5, 50, 'rojo'),
    (4.5, 24, 'verde'),
])
def test_bordes_de_la_regla_rf34(umbrales, nota, pct, esperado):
    assert clasificar_semaforo(nota, pct) == esperado


@pytest.mark.django_db
def test_sin_actividades_es_verde_aunque_la_nota_sea_cero(umbrales):
    assert clasificar_semaforo(0, 0, tiene_actividades=False) == 'verde'


@pytest.mark.django_db
@pytest.mark.parametrize('avance,nota,esperado', [
    (59, 2.95, 'rojo'),
    (60, 3.0, 'amarillo'),
    (69, 3.45, 'amarillo'),
    (70, 3.5, 'verde'),
])
def test_bordes_calculados_desde_avances_reales(director, umbrales, avance, nota, esperado):
    curso = CursoFactory()
    proyecto = ProyectoFactory(id_curso=curso)
    est = _inscribir(curso, proyecto, completadas=2, pendientes=0, avance=avance)

    r = director.get(f'/api/reportes/estudiantes/{est.id}/rendimiento/', {'proyecto_id': proyecto.id})
    assert r.status_code == 200, r.data
    assert r.data['indicadores']['nota_promedio'] == nota
    assert r.data['indicadores']['nivel_semaforo'] == esperado


# ── Filtro ?nivel= ─────────────────────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('nivel,esperados', [
    ('rojo', {'rojo'}),
    ('amarillo', {'amarillo'}),
    ('verde', {'verde', 'verde_sin_actividades'}),
])
def test_filtro_por_nivel_devuelve_solo_ese_color(director, escenario, nivel, esperados):
    r = director.get(URL, {'curso_id': escenario['curso'].id, 'nivel': nivel})
    assert r.status_code == 200
    assert {e['id'] for e in r.data['estudiantes']} == {escenario[k].id for k in esperados}
    assert all(e['nivel_semaforo'] == nivel for e in r.data['estudiantes'])
    assert r.data['total'] == len(esperados)


@pytest.mark.django_db
@pytest.mark.parametrize('nivel', ['xyz', 'ROJO', 'naranja'])
def test_nivel_invalido_retorna_400(director, nivel):
    r = director.get(URL, {'nivel': nivel})
    assert r.status_code == 400
    assert 'nivel' in r.data['error']


@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['estudiante', 'lider_equipo'])
def test_estudiante_y_lider_reciben_403(escenario, rol):
    cliente = _cliente(UsuarioFactory(tipo_rol=rol))
    assert cliente.get(URL, {'nivel': 'rojo'}).status_code == 403


@pytest.mark.django_db
def test_sin_autenticar_retorna_401():
    assert APIClient().get(URL).status_code == 401


@pytest.mark.django_db
def test_consulta_con_nivel_queda_en_bitacora(director, escenario):
    curso_id = escenario['curso'].id
    director.get(URL, {'curso_id': curso_id, 'nivel': 'rojo'})
    assert BitacoraSistema.objects.filter(
        modulo='reportes', accion=BitacoraSistema.Accion.ACCESS,
        descripcion__contains=f'curso={curso_id}',
    ).filter(descripcion__contains='nivel=rojo').exists()


# ── Regresión: vistas que consumían en_riesgo ──────────────────────────────

@pytest.mark.django_db
def test_estudiantes_riesgo_docente_sin_nivel_sigue_devolviendo_solo_rojos(docente, escenario):
    """EstudiantesRiesgo.jsx llama sin ?nivel= y filtra por e.en_riesgo."""
    r = docente.get(URL, {'curso_id': escenario['curso'].id})
    assert r.status_code == 200
    assert [e['id'] for e in r.data['estudiantes']] == [escenario['rojo'].id]
    est = r.data['estudiantes'][0]
    assert CAMPOS_ESTUDIANTE <= set(est)
    assert est['en_riesgo'] is True
    assert est['alertas']


@pytest.mark.django_db
def test_solo_riesgo_false_trae_todos_y_en_riesgo_equivale_a_rojo(docente, escenario):
    r = docente.get(URL, {'curso_id': escenario['curso'].id, 'solo_riesgo': 'false'})
    assert r.status_code == 200
    assert r.data['total'] == 4
    for est in r.data['estudiantes']:
        assert CAMPOS_ESTUDIANTE <= set(est)
        assert est['en_riesgo'] is (est['nivel_semaforo'] == 'rojo')


@pytest.mark.django_db
def test_riesgo_director_por_periodo(director, escenario):
    """EstudiantesRiesgoDirector.jsx filtra por periodo y ordena por nota y % incumplidas."""
    periodo_id = escenario['curso'].id_periodo_academico_id
    r = director.get(URL, {'periodo_id': periodo_id, 'solo_riesgo': 'false'})
    assert r.status_code == 200
    por_id = {e['id']: e for e in r.data['estudiantes']}
    assert por_id[escenario['rojo'].id]['nota_promedio'] == 0.0
    assert por_id[escenario['rojo'].id]['porcentaje_actividades_incumplidas'] == 100.0
    assert por_id[escenario['amarillo'].id]['porcentaje_actividades_incumplidas'] == 25.0


@pytest.mark.django_db
def test_perfil_de_rendimiento_como_docente(docente, escenario):
    est = escenario['rojo']
    r = docente.get(f'/api/reportes/estudiantes/{est.id}/rendimiento/',
                    {'proyecto_id': escenario['proyecto'].id})
    assert r.status_code == 200, r.data
    assert r.data['estudiante']['id'] == est.id
    ind = r.data['indicadores']
    assert (ind['nivel_semaforo'], ind['en_riesgo']) == ('rojo', True)
    assert len(ind['alertas']) == 2   # nota y % incumplidas
    assert 'comparativo_grupo' in r.data


@pytest.mark.django_db
def test_estudiante_ve_su_perfil_pero_no_el_de_otro(escenario):
    propio = escenario['amarillo']
    cliente = _cliente(propio)
    r = cliente.get(f'/api/reportes/estudiantes/{propio.id}/rendimiento/')
    assert r.status_code == 200
    assert r.data['indicadores']['nivel_semaforo'] == 'amarillo'
    assert r.data['indicadores']['en_riesgo'] is False

    otro = escenario['rojo']
    assert cliente.get(f'/api/reportes/estudiantes/{otro.id}/rendimiento/').status_code == 403


@pytest.mark.django_db
def test_perfil_de_estudiante_inexistente_retorna_404(director, umbrales):
    assert director.get('/api/reportes/estudiantes/999999/rendimiento/').status_code == 404


@pytest.mark.django_db
def test_pdf_del_estudiante_se_genera_y_descarga(docente, escenario, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    r = docente.post('/api/exportar/reporte/', {
        'tipo_reporte': 'estudiante', 'formato': 'pdf',
        'parametros': {'estudiante_id': escenario['rojo'].id, 'proyecto_id': escenario['proyecto'].id},
    }, format='json')
    assert r.status_code == 201, r.data
    assert r.data['estado'] == 'listo', r.data['mensaje_error']

    descarga = docente.get(f"/api/exportar/{r.data['id']}/descargar/")
    assert descarga.status_code == 200
    assert descarga['Content-Type'] == 'application/pdf'
    assert b''.join(descarga.streaming_content).startswith(b'%PDF')


# ── Rendimiento del filtro del director ────────────────────────────────────
# El "< 3 s" de la aceptación se mide a mano en la app desplegada: aquí la BD de
# pruebas está en Supabase y cada consulta cuesta ~80 ms de red desde el equipo
# local, así que el tiempo no es representativo. Se mide lo que sí depende del
# código: cuántas consultas hace el endpoint según el número de estudiantes.

def _consultas_bajo_rendimiento(cliente, curso):
    filtros = {'curso_id': curso.id, 'periodo_id': curso.id_periodo_academico_id, 'nivel': 'rojo'}
    with CaptureQueriesContext(connection) as consultas:
        inicio = time.perf_counter()
        r = cliente.get(URL, filtros)
        duracion = time.perf_counter() - inicio
    assert r.status_code == 200
    return len(consultas), duracion, r.data['total']


def _completar_curso(escenario, total):
    curso, proyecto = escenario['curso'], escenario['proyecto']
    while CursoEstudiante.objects.filter(curso=curso).count() < total:
        _inscribir(curso, proyecto, completadas=2, pendientes=0, avance=100)


@pytest.mark.django_db
def test_filtro_del_director_devuelve_los_rojos_de_un_curso_de_30(director, escenario):
    _completar_curso(escenario, 30)
    n, duracion, total = _consultas_bajo_rendimiento(director, escenario['curso'])
    print(f'\n[HU-029] bajo-rendimiento con 30 estudiantes: {n} consultas, {duracion:.2f} s')
    assert total == 1


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason='Hallazgo PRB-09: bajo-rendimiento hace 6 consultas por estudiante (N+1)')
def test_consultas_no_crecen_con_el_numero_de_estudiantes(director, escenario):
    _completar_curso(escenario, 10)
    con_10, _, _ = _consultas_bajo_rendimiento(director, escenario['curso'])
    _completar_curso(escenario, 30)
    con_30, _, _ = _consultas_bajo_rendimiento(director, escenario['curso'])
    print(f'\n[HU-029] consultas: 10 estudiantes = {con_10}, 30 estudiantes = {con_30}')
    # 20 estudiantes más no deberían sumar más de un puñado de consultas
    assert con_30 - con_10 <= 5
