"""
HU-033 — Pruebas de regresión de la vista semafórica unificada (SCRUM-601).

A diferencia de test_hu033_indicadores.py (servicio simulado con mocks), aquí
se arma un escenario real en BD y se llama a los endpoints por URL para
verificar que:
  - la suma de distribucion_semaforo es igual al total de estudiantes del filtro
    (sin filtro, por curso y por periodo);
  - estudiantes_en_riesgo de cada curso es igual a los estudiantes en rojo;
  - el nivel de un mismo estudiante coincide en indicadores, bajo-rendimiento,
    reporte de proyecto y perfil de rendimiento;
  - el docente sigue sin acceso (403) y la consulta queda en bitácora.

Escenario (umbrales por defecto RF34):
  Periodo 1
    Curso A: rojo_a1, rojo_a2, amarillo_a, verde_a
    Curso B: rojo_b, verde_b_sin_actividades
  Periodo 2
    Curso C: amarillo_c
"""
import pytest
from rest_framework.test import APIClient

from apps.bitacora.models import BitacoraSistema
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad, CursoEstudiante
from tests.factories import (
    ActividadFactory, AdminFactory, CursoFactory, DocenteFactory, EquipoFactory,
    FaseProyectoFactory, MiembroEquipoFactory, PeriodoAcademicoFactory,
    ProyectoFactory, UsuarioFactory,
)

URL_INDICADORES = '/api/reportes/indicadores/'
URL_BAJO_RENDIMIENTO = '/api/reportes/bajo-rendimiento/'


def _inscribir(curso, proyecto=None, completadas=0, pendientes=0, avance=0):
    """
    Crea un estudiante inscrito en el curso. Si hay actividades, el estudiante
    va en su propio equipo del proyecto para que sus actividades no se mezclen
    con las de los demás. avance = porcentaje_completado de cada avance.
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


def _rojo(curso, proyecto):
    # nota 0.0 y 100 % incumplidas
    return _inscribir(curso, proyecto, completadas=0, pendientes=2, avance=0)


def _amarillo(curso, proyecto):
    # nota 5.0 y 25 % incumplidas (borde de amarillo)
    return _inscribir(curso, proyecto, completadas=3, pendientes=1, avance=100)


def _verde(curso, proyecto):
    # nota 5.0 y 0 % incumplidas
    return _inscribir(curso, proyecto, completadas=2, pendientes=0, avance=100)


@pytest.fixture
def escenario(db):
    # Equipo.clean() exige este parámetro para validar cupo_maximo
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '10', 'categoria': ParametroSistema.Categoria.GENERAL,
                  'tipo_dato': ParametroSistema.TipoDato.INTEGER},
    )
    p1 = PeriodoAcademicoFactory()
    p2 = PeriodoAcademicoFactory()
    curso_a = CursoFactory(id_periodo_academico=p1, nombre='Curso A')
    curso_b = CursoFactory(id_periodo_academico=p1, nombre='Curso B')
    curso_c = CursoFactory(id_periodo_academico=p2, nombre='Curso C')
    proy_a = ProyectoFactory(id_curso=curso_a)
    proy_b = ProyectoFactory(id_curso=curso_b)
    proy_c = ProyectoFactory(id_curso=curso_c)

    return {
        'p1': p1, 'p2': p2,
        'curso_a': curso_a, 'curso_b': curso_b, 'curso_c': curso_c,
        'proy_a': proy_a, 'proy_b': proy_b, 'proy_c': proy_c,
        'rojo_a1': _rojo(curso_a, proy_a),
        'rojo_a2': _rojo(curso_a, proy_a),
        'amarillo_a': _amarillo(curso_a, proy_a),
        'verde_a': _verde(curso_a, proy_a),
        'rojo_b': _rojo(curso_b, proy_b),
        'verde_b_sin_actividades': _inscribir(curso_b),
        'amarillo_c': _amarillo(curso_c, proy_c),
    }


@pytest.fixture
def director():
    cliente = APIClient()
    cliente.force_authenticate(user=UsuarioFactory(tipo_rol='director'))
    return cliente


def _indicadores(cliente, **filtros):
    r = cliente.get(URL_INDICADORES, filtros)
    assert r.status_code == 200, r.data
    return r.data


# ── Distribución semafórica vs. total del filtro ────────────────────────────

@pytest.mark.django_db
def test_suma_distribucion_es_total_de_estudiantes_sin_filtro(director, escenario):
    data = _indicadores(director)
    assert sum(data['distribucion_semaforo'].values()) == 7
    assert data['distribucion_semaforo'] == {'verde': 2, 'amarillo': 2, 'rojo': 3}


@pytest.mark.django_db
def test_distribucion_filtrada_por_curso(director, escenario):
    data = _indicadores(director, curso_id=escenario['curso_a'].id)
    assert data['filtros_aplicados']['curso_id'] == escenario['curso_a'].id
    assert sum(data['distribucion_semaforo'].values()) == 4
    assert data['distribucion_semaforo'] == {'verde': 1, 'amarillo': 1, 'rojo': 2}


@pytest.mark.django_db
@pytest.mark.parametrize('periodo,esperado', [
    ('p1', {'verde': 2, 'amarillo': 1, 'rojo': 3}),
    ('p2', {'verde': 0, 'amarillo': 1, 'rojo': 0}),
])
def test_distribucion_filtrada_por_periodo(director, escenario, periodo, esperado):
    data = _indicadores(director, periodo_id=escenario[periodo].id)
    assert data['distribucion_semaforo'] == esperado
    assert sum(data['distribucion_semaforo'].values()) == sum(esperado.values())


@pytest.mark.django_db
def test_distribucion_filtrada_por_curso_y_periodo(director, escenario):
    data = _indicadores(director, periodo_id=escenario['p1'].id, curso_id=escenario['curso_b'].id)
    assert data['distribucion_semaforo'] == {'verde': 1, 'amarillo': 0, 'rojo': 1}


@pytest.mark.django_db
def test_curso_de_otro_periodo_devuelve_distribucion_vacia(director, escenario):
    data = _indicadores(director, periodo_id=escenario['p2'].id, curso_id=escenario['curso_a'].id)
    assert data['distribucion_semaforo'] == {'verde': 0, 'amarillo': 0, 'rojo': 0}
    assert data['estudiantes_riesgo_por_curso'] == []


# ── estudiantes_en_riesgo por curso = estudiantes en rojo ──────────────────

@pytest.mark.django_db
def test_estudiantes_en_riesgo_por_curso_es_igual_a_rojos(director, escenario):
    data = _indicadores(director, periodo_id=escenario['p1'].id)
    filas = {f['curso_id']: f for f in data['estudiantes_riesgo_por_curso']}

    fila_a = filas[escenario['curso_a'].id]
    assert (fila_a['verde'], fila_a['amarillo'], fila_a['rojo']) == (1, 1, 2)
    assert fila_a['estudiantes_en_riesgo'] == fila_a['rojo'] == 2

    fila_b = filas[escenario['curso_b'].id]
    assert (fila_b['verde'], fila_b['amarillo'], fila_b['rojo']) == (1, 0, 1)
    assert fila_b['estudiantes_en_riesgo'] == fila_b['rojo'] == 1

    # Ordenado de mayor a menor riesgo, y la suma por curso cuadra con la distribución
    assert [f['curso_id'] for f in data['estudiantes_riesgo_por_curso']] == [
        escenario['curso_a'].id, escenario['curso_b'].id]
    assert sum(f['rojo'] for f in filas.values()) == data['distribucion_semaforo']['rojo']


@pytest.mark.django_db
@pytest.mark.parametrize('curso', ['curso_a', 'curso_b', 'curso_c'])
def test_riesgo_por_curso_coincide_con_bajo_rendimiento_nivel_rojo(director, escenario, curso):
    curso_id = escenario[curso].id
    data = _indicadores(director, curso_id=curso_id)
    en_riesgo = sum(f['estudiantes_en_riesgo'] for f in data['estudiantes_riesgo_por_curso'])

    r = director.get(URL_BAJO_RENDIMIENTO, {'curso_id': curso_id, 'nivel': 'rojo'})
    assert r.status_code == 200
    assert r.data['total'] == en_riesgo == data['distribucion_semaforo']['rojo']


# ── Mismo estudiante, mismo color en todas las vistas ──────────────────────

@pytest.mark.django_db
def test_mismo_nivel_en_indicadores_bajo_rendimiento_reporte_y_perfil(director, escenario):
    curso_a, proy_a = escenario['curso_a'], escenario['proy_a']
    esperados = {
        escenario['rojo_a1'].id: 'rojo',
        escenario['rojo_a2'].id: 'rojo',
        escenario['amarillo_a'].id: 'amarillo',
        escenario['verde_a'].id: 'verde',
    }

    # Panel de riesgo (director / docente)
    r = director.get(URL_BAJO_RENDIMIENTO, {'curso_id': curso_a.id, 'solo_riesgo': 'false'})
    assert r.status_code == 200
    assert {e['id']: e['nivel_semaforo'] for e in r.data['estudiantes']} == esperados

    # Reporte de proyecto
    r = director.get(f'/api/reportes/proyecto/{proy_a.id}/')
    assert r.status_code == 200, r.data
    niveles_reporte = {e['usuario_id']: e['nivel_semaforo'] for e in r.data['avance_por_estudiante']}
    assert niveles_reporte == esperados
    assert {e['usuario_id'] for e in r.data['estudiantes_bajo_rendimiento']} == {
        escenario['rojo_a1'].id, escenario['rojo_a2'].id}

    # Perfil de rendimiento de cada estudiante
    for est_id, nivel in esperados.items():
        r = director.get(f'/api/reportes/estudiantes/{est_id}/rendimiento/', {'proyecto_id': proy_a.id})
        assert r.status_code == 200, r.data
        assert r.data['indicadores']['nivel_semaforo'] == nivel
        assert r.data['indicadores']['en_riesgo'] is (nivel == 'rojo')


@pytest.mark.django_db
def test_umbral_editado_cambia_el_color_en_indicadores(director, escenario):
    curso_id = escenario['curso_a'].id
    assert _indicadores(director, curso_id=curso_id)['distribucion_semaforo']['amarillo'] == 1

    # Con 30 % como umbral de alerta, el estudiante con 25 % incumplidas pasa a verde
    ParametroSistema.objects.update_or_create(
        clave='umbral_porcentaje_alerta',
        defaults={'valor': '30', 'categoria': 'rendimiento', 'tipo_dato': 'integer'},
    )
    data = _indicadores(director, curso_id=curso_id)
    assert data['distribucion_semaforo'] == {'verde': 2, 'amarillo': 0, 'rojo': 2}


# ── Permisos, validación y bitácora ────────────────────────────────────────

@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['docente', 'estudiante', 'lider_equipo'])
def test_roles_sin_permiso_reciben_403(rol):
    cliente = APIClient()
    usuario = DocenteFactory() if rol == 'docente' else UsuarioFactory(tipo_rol=rol)
    cliente.force_authenticate(user=usuario)
    assert cliente.get(URL_INDICADORES).status_code == 403


@pytest.mark.django_db
def test_sin_autenticar_retorna_401():
    assert APIClient().get(URL_INDICADORES).status_code == 401


@pytest.mark.django_db
def test_administrador_ve_la_misma_distribucion_que_el_director(director, escenario):
    admin = APIClient()
    admin.force_authenticate(user=AdminFactory())
    filtros = {'periodo_id': escenario['p1'].id}
    assert _indicadores(admin, **filtros)['distribucion_semaforo'] == \
        _indicadores(director, **filtros)['distribucion_semaforo']


@pytest.mark.django_db
def test_curso_id_no_entero_retorna_400(director):
    assert director.get(URL_INDICADORES, {'curso_id': 'abc'}).status_code == 400


@pytest.mark.django_db
def test_consulta_de_indicadores_queda_en_bitacora(director, escenario):
    curso_id = escenario['curso_a'].id
    _indicadores(director, curso_id=curso_id)
    assert BitacoraSistema.objects.filter(
        modulo='reportes',
        accion=BitacoraSistema.Accion.ACCESS,
        descripcion__contains=f'curso={curso_id}',
    ).exists()
