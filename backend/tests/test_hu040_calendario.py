"""
HU-040 — Calendario unificado (SCRUM-527), detalle de evento (SCRUM-530)
y recordatorios de vencimiento en 48 h (SCRUM-528).
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.alertas.models import Alerta, ColaCorreo
from apps.calendario.services import calcular_urgencia
from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad, HitoProyecto
from tests.factories import (ActividadFactory, CursoFactory, DocenteFactory, EquipoFactory,
                             FaseProyectoFactory, MiembroEquipoFactory, ProyectoFactory,
                             UsuarioFactory)

URL = '/api/calendario/'
HOY = date.today()


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


def _cliente(usuario):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c


def _proyecto_con_equipo(estudiante, nombre_curso):
    """Curso -> proyecto -> fase -> equipo con el estudiante como miembro activo."""
    curso = CursoFactory(nombre=nombre_curso)
    proyecto = ProyectoFactory(id_curso=curso, nombre=f'Proyecto {nombre_curso}')
    fase = FaseProyectoFactory(id_proyecto=proyecto)
    equipo = EquipoFactory(proyecto=proyecto)
    MiembroEquipoFactory(equipo=equipo, usuario=estudiante)
    return proyecto, fase, equipo


def _hito(proyecto, fecha_fin, tipo='entrega', estado='pendiente'):
    return HitoProyecto.objects.create(
        id_proyecto=proyecto, nombre=f'{tipo} {fecha_fin}', fecha_inicio=fecha_fin,
        fecha_fin=fecha_fin, tipo=tipo, estado=estado)


def _rango(dias_antes=10, dias_despues=10):
    return {'desde': (HOY - timedelta(days=dias_antes)).isoformat(),
            'hasta': (HOY + timedelta(days=dias_despues)).isoformat()}


# ── Urgencia ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('dias, completado, esperado', [
    (-1, False, 'vencido'),
    (-1, True, 'normal'),
    (0, False, 'proximo'),
    (2, False, 'proximo'),
    (3, False, 'normal'),
    (1, True, 'normal'),
])
def test_calcular_urgencia(dias, completado, esperado):
    assert calcular_urgencia(HOY + timedelta(days=dias), completado, HOY) == esperado


# ── SCRUM-527: GET /api/calendario/ ──────────────────────────────────────────

@pytest.mark.django_db
def test_estudiante_de_dos_cursos_ve_eventos_de_ambos():
    est = UsuarioFactory()
    p1, f1, e1 = _proyecto_con_equipo(est, 'Ingeniería de Software')
    p2, f2, e2 = _proyecto_con_equipo(est, 'Bases de Datos')
    _hito(p1, HOY + timedelta(days=5), tipo='revision')
    ActividadFactory(id_fase=f2, id_equipo_asignado=e2, fecha_limite=HOY + timedelta(days=1))

    r = _cliente(est).get(URL, _rango())

    assert r.status_code == 200
    cursos = {e['curso_nombre'] for e in r.data['eventos']}
    assert cursos == {'Ingeniería de Software', 'Bases de Datos'}
    assert r.data['total'] == 2
    revision = next(e for e in r.data['eventos'] if e['tipo'] == 'revision')
    assert set(revision) == {'id', 'tipo', 'titulo', 'fecha', 'urgencia',
                             'proyecto_id', 'proyecto_nombre', 'curso_nombre'}
    assert revision['id'].startswith('hito-') and revision['proyecto_id'] == p1.id


@pytest.mark.django_db
def test_urgencia_de_los_eventos_sigue_la_regla():
    est = UsuarioFactory()
    proyecto, fase, equipo = _proyecto_con_equipo(est, 'Curso A')
    vencida = ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY - timedelta(days=1))
    completada = ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY - timedelta(days=1),
                                  estado=Actividad.Estado.COMPLETADA)
    proxima = ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY + timedelta(days=2))
    lejana = ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY + timedelta(days=6))

    eventos = {e['id']: e['urgencia'] for e in _cliente(est).get(URL, _rango()).data['eventos']}

    assert eventos == {
        f'actividad-{vencida.id}': 'vencido',
        f'actividad-{completada.id}': 'normal',
        f'actividad-{proxima.id}': 'proximo',
        f'actividad-{lejana.id}': 'normal',
    }


@pytest.mark.django_db
def test_estudiante_no_ve_actividades_de_otro_equipo_ni_de_otros_cursos():
    est = UsuarioFactory()
    proyecto, fase, equipo = _proyecto_con_equipo(est, 'Curso A')
    otro_equipo = EquipoFactory(proyecto=proyecto)
    propia = ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, fecha_limite=HOY)
    ActividadFactory(id_fase=fase, id_equipo_asignado=otro_equipo, fecha_limite=HOY)
    ActividadFactory(fecha_limite=HOY)  # proyecto ajeno

    ids = [e['id'] for e in _cliente(est).get(URL, _rango()).data['eventos']]

    assert ids == [f'actividad-{propia.id}']


@pytest.mark.django_db
def test_docente_ve_solo_sus_cursos_y_director_todos():
    docente = DocenteFactory()
    mia = ActividadFactory(id_fase__id_proyecto__id_curso__id_docente=docente, fecha_limite=HOY)
    ajena = ActividadFactory(fecha_limite=HOY)

    ids_docente = {e['id'] for e in _cliente(docente).get(URL, _rango()).data['eventos']}
    ids_director = {e['id'] for e in _cliente(UsuarioFactory(tipo_rol='director')).get(URL, _rango()).data['eventos']}

    assert ids_docente == {f'actividad-{mia.id}'}
    assert ids_director == {f'actividad-{mia.id}', f'actividad-{ajena.id}'}


@pytest.mark.django_db
def test_filtra_por_rango_y_por_defecto_usa_el_mes_actual():
    docente = DocenteFactory()
    fase = FaseProyectoFactory(id_proyecto__id_curso__id_docente=docente)
    dentro = ActividadFactory(id_fase=fase, fecha_limite=HOY.replace(day=1))
    ActividadFactory(id_fase=fase, fecha_limite=HOY.replace(day=1) - timedelta(days=1))

    r = _cliente(docente).get(URL)

    assert r.status_code == 200
    assert r.data['desde'] == HOY.replace(day=1).isoformat()
    assert [e['id'] for e in r.data['eventos']] == [f'actividad-{dentro.id}']


@pytest.mark.django_db
@pytest.mark.parametrize('params', [
    {'desde': '2026-01-01', 'hasta': '2026-04-11'},   # 100 días
    {'desde': '2026-03-10', 'hasta': '2026-03-01'},   # desde > hasta
    {'desde': '10/03/2026', 'hasta': '2026-03-20'},   # formato inválido
])
def test_rango_invalido_retorna_400(params):
    r = _cliente(UsuarioFactory()).get(URL, params)
    assert r.status_code == 400
    assert 'detail' in r.data


@pytest.mark.django_db
def test_rango_de_92_dias_se_acepta():
    r = _cliente(UsuarioFactory()).get(URL, {'desde': '2026-01-01', 'hasta': '2026-04-03'})
    assert r.status_code == 200


def test_sin_autenticar_retorna_401(db):
    assert APIClient().get(URL).status_code == 401


# ── SCRUM-530: GET /api/calendario/<evento_id>/ ──────────────────────────────

@pytest.mark.django_db
def test_detalle_de_actividad_propia():
    est = UsuarioFactory(nombre='Ana', apellido='Rojas')
    proyecto, fase, equipo = _proyecto_con_equipo(est, 'Curso A')
    act = ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, fecha_limite=HOY + timedelta(days=1))
    AvanceActividad.objects.create(id_actividad=act, id_usuario=est, descripcion='a', porcentaje_completado=30)
    AvanceActividad.objects.create(id_actividad=act, id_usuario=est, descripcion='b', porcentaje_completado=60)

    r = _cliente(est).get(f'{URL}actividad-{act.id}/')

    assert r.status_code == 200
    assert r.data['id'] == f'actividad-{act.id}' and r.data['urgencia'] == 'proximo'
    assert r.data['porcentaje_avance'] == 60
    assert r.data['equipo'] == {'nombre': equipo.nombre, 'miembros': ['Ana Rojas']}
    assert r.data['enlace'] == f'/estudiante/proyectos/{proyecto.id}/actividades/{act.id}/entregables'


@pytest.mark.django_db
def test_detalle_de_hito_usa_el_progreso_del_proyecto():
    docente = DocenteFactory()
    proyecto = ProyectoFactory(id_curso__id_docente=docente)
    hito = _hito(proyecto, HOY + timedelta(days=10), tipo='revision')

    with patch('apps.cursos.models.VistaProgresoProyecto.objects') as vista:
        vista.filter.return_value.values_list.return_value.first.return_value = 45
        r = _cliente(docente).get(f'{URL}hito-{hito.id}/')

    assert r.status_code == 200
    assert r.data['tipo'] == 'revision' and r.data['porcentaje_avance'] == 45
    assert r.data['equipo'] is None
    assert r.data['enlace'] == f'/docente/proyectos/{proyecto.id}/cronograma'


@pytest.mark.django_db
def test_detalle_de_evento_ajeno_retorna_404():
    est = UsuarioFactory()
    proyecto, fase, equipo = _proyecto_con_equipo(est, 'Curso A')
    otro_equipo = EquipoFactory(proyecto=proyecto)
    de_otro_equipo = ActividadFactory(id_fase=fase, id_equipo_asignado=otro_equipo)
    de_otro_proyecto = ActividadFactory()
    hito_ajeno = _hito(ProyectoFactory(), HOY)

    cliente = _cliente(est)
    for evento in (f'actividad-{de_otro_equipo.id}', f'actividad-{de_otro_proyecto.id}', f'hito-{hito_ajeno.id}'):
        assert cliente.get(f'{URL}{evento}/').status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize('evento_id', ['actividad-999999', 'tarea-1', 'actividad-abc', 'hito'])
def test_detalle_inexistente_o_mal_formado_retorna_404(evento_id):
    r = _cliente(UsuarioFactory(tipo_rol='director')).get(f'{URL}{evento_id}/')
    assert r.status_code == 404


# ── SCRUM-528: recordatorios de vencimiento en 48 h ──────────────────────────

@pytest.mark.django_db
def test_run_scheduler_crea_recordatorios_48h_sin_duplicar():
    est, companero = UsuarioFactory(), UsuarioFactory()
    proyecto, fase, equipo = _proyecto_con_equipo(est, 'Curso A')
    MiembroEquipoFactory(equipo=equipo, usuario=companero)
    hoy = ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY)
    en_2_dias = ActividadFactory(id_fase=fase, id_equipo_asignado=equipo, fecha_limite=HOY + timedelta(days=2))
    ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY + timedelta(days=3))  # fuera de 48 h
    ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY,
                     estado=Actividad.Estado.COMPLETADA)  # ya completada

    call_command('run_scheduler', '--once')
    call_command('run_scheduler', '--once')

    recordatorios = Alerta.objects.filter(tipo='recordatorio_vencimiento')
    assert sorted(recordatorios.values_list('referencia_id', 'id_usuario_destino_id')) == sorted([
        (hoy.id, est.id),                                       # responsable
        (en_2_dias.id, est.id), (en_2_dias.id, companero.id),   # sin responsable -> miembros del equipo
    ])
    assert set(recordatorios.values_list('gravedad', flat=True)) == {'baja'}
    correos = ColaCorreo.objects.filter(plantilla='recordatorio')
    assert correos.count() == 3
    # Un solo correo por recordatorio: ninguno con plantilla 'alerta' para estos mensajes
    mensajes_alerta = [c.contexto.get('mensaje', '') for c in ColaCorreo.objects.filter(plantilla='alerta')]
    assert not any(' vence ' in m for m in mensajes_alerta)
