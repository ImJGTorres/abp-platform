"""
HU-041 — Semáforo personal del estudiante (SCRUM-545) con los umbrales RF34 compartidos (SCRUM-546).
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from apps.configuracion.models import ParametroSistema
from apps.cursos.models import Actividad, AvanceActividad
from apps.entregables.models import Entregable
from apps.reportes.semaforo import semaforo_estudiante
from apps.reportes.services import calcular_rendimiento_estudiante, get_estudiantes_bajo_rendimiento
from tests.factories import (ActividadFactory, DocenteFactory, EquipoFactory, FaseProyectoFactory,
                             MiembroEquipoFactory, UsuarioFactory)

URL = '/api/reportes/semaforos/estudiante/'
HOY = date.today()


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def entorno():
    """Estudiante miembro activo de un equipo en un proyecto."""
    est = UsuarioFactory()
    fase = FaseProyectoFactory()
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=equipo, usuario=est)
    return est, fase, equipo


def _actividad(fase, equipo, dias, estado=Actividad.Estado.PENDIENTE, nombre=None):
    kwargs = {'nombre': nombre} if nombre else {}
    return ActividadFactory(id_fase=fase, id_equipo_asignado=equipo,
                            fecha_limite=HOY + timedelta(days=dias), estado=estado, **kwargs)


def _avance(actividad, usuario, porcentaje):
    AvanceActividad.objects.create(id_actividad=actividad, id_usuario=usuario,
                                   descripcion='avance', porcentaje_completado=porcentaje)


def _get(usuario, **params):
    c = APIClient()
    c.force_authenticate(user=usuario)
    return c.get(URL, params)


# ── SCRUM-545 ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_estudiante_al_dia_verde_sin_criticos(entorno):
    est, fase, equipo = entorno
    hecha = _actividad(fase, equipo, 10, estado=Actividad.Estado.COMPLETADA)
    _avance(hecha, est, 100)

    r = _get(est)

    assert r.status_code == 200
    assert r.data['nivel'] == 'verde'
    assert r.data['nota_promedio'] == 5.0 and r.data['porcentaje_actividades_incumplidas'] == 0
    assert r.data['entregables_criticos'] == []
    assert r.data['recomendaciones'] == ['Vas al día; mantén el ritmo']


@pytest.mark.django_db
def test_estudiante_con_2_vencidas_tiene_2_criticos_y_recomendacion(entorno):
    est, fase, equipo = entorno
    primera = _actividad(fase, equipo, -5, nombre='Modelo entidad-relación')
    _actividad(fase, equipo, -1, nombre='Diagrama de clases')
    hecha = _actividad(fase, equipo, -10, estado=Actividad.Estado.COMPLETADA)
    _avance(hecha, est, 100)
    _actividad(fase, equipo, 20)  # lejana: no es crítica

    r = _get(est)

    assert r.status_code == 200
    assert r.data['nivel'] in ('amarillo', 'rojo')
    criticos = r.data['entregables_criticos']
    assert [c['titulo'] for c in criticos] == ['Modelo entidad-relación', 'Diagrama de clases']
    assert {c['estado'] for c in criticos} == {'vencida'}
    assert criticos[0] == {
        'titulo': 'Modelo entidad-relación',
        'fecha': primera.fecha_limite.isoformat(),
        'estado': 'vencida',
        'enlace': f'/estudiante/proyectos/{fase.id_proyecto_id}/actividades/{primera.id}/entregables',
    }
    assert 'Tienes 2 actividades vencidas; empieza por «Modelo entidad-relación»' in r.data['recomendaciones']


@pytest.mark.django_db
def test_por_vencer_en_3_dias_y_rechazados_son_criticos(entorno):
    est, fase, equipo = entorno
    proxima = _actividad(fase, equipo, 3, nombre='Informe parcial')
    _actividad(fase, equipo, 4)  # fuera de los 3 días
    _avance(proxima, est, 90)
    rechazado = Entregable.objects.create(id_actividad=proxima, id_equipo=equipo, titulo='Informe v1',
                                          descripcion='x', tipo='documento', estado='rechazado')

    r = _get(est)

    assert [(c['titulo'], c['estado']) for c in r.data['entregables_criticos']] == [
        ('Informe parcial', 'por_vencer'), (rechazado.titulo, 'rechazado')]
    assert 'Corrige y reenvía «Informe v1»' in r.data['recomendaciones']


@pytest.mark.django_db
def test_recomienda_subir_el_promedio_con_el_umbral_incumplido(entorno):
    est, fase, equipo = entorno
    hecha = _actividad(fase, equipo, -2, estado=Actividad.Estado.COMPLETADA)
    _avance(hecha, est, 64)  # 3.2 → entre 3.0 y 3.5

    r = _get(est)

    assert r.data['nivel'] == 'amarillo'
    assert 'Tu promedio (3.2) está por debajo de 3.5' in r.data['recomendaciones']


@pytest.mark.django_db
def test_lider_de_equipo_tambien_consulta(entorno):
    _, fase, equipo = entorno
    lider = UsuarioFactory(tipo_rol='lider_equipo')
    MiembroEquipoFactory(equipo=equipo, usuario=lider)
    assert _get(lider).status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('rol', ['docente', 'director', 'administrador'])
def test_otros_roles_reciben_403(rol):
    r = _get(UsuarioFactory(tipo_rol=rol))
    assert r.status_code == 403


@pytest.mark.django_db
def test_siempre_usa_el_usuario_autenticado(entorno):
    est, fase, equipo = entorno
    otro = UsuarioFactory()
    otro_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=otro_equipo, usuario=otro)
    _actividad(fase, otro_equipo, -3)  # vencida del otro estudiante

    r = _get(est, estudiante_id=otro.id)  # el parámetro se ignora

    assert r.status_code == 200
    assert r.data['entregables_criticos'] == []


@pytest.mark.django_db
def test_proyecto_id_filtra_y_proyecto_ajeno_da_403(entorno):
    est, fase, equipo = entorno
    _actividad(fase, equipo, -1, nombre='Del proyecto A')
    fase_b = FaseProyectoFactory()
    equipo_b = EquipoFactory(proyecto=fase_b.id_proyecto)
    MiembroEquipoFactory(equipo=equipo_b, usuario=est)
    _actividad(fase_b, equipo_b, -1, nombre='Del proyecto B')

    r = _get(est, proyecto_id=fase.id_proyecto_id)
    assert [c['titulo'] for c in r.data['entregables_criticos']] == ['Del proyecto A']

    ajeno = FaseProyectoFactory().id_proyecto_id
    assert _get(est, proyecto_id=ajeno).status_code == 403
    assert _get(est, proyecto_id='abc').status_code == 400


def test_sin_autenticar_retorna_401(db):
    assert APIClient().get(URL).status_code == 401


# ── SCRUM-546: mismos umbrales que HU-029 / HU-033 ───────────────────────────

@pytest.mark.django_db
def test_cambiar_un_umbral_cambia_el_color_en_todos_los_reportes(entorno):
    est, fase, equipo = entorno
    hecha = _actividad(fase, equipo, -2, estado=Actividad.Estado.COMPLETADA)
    _avance(hecha, est, 64)  # nota 3.2

    def niveles():
        hu029 = next(e for e in get_estudiantes_bajo_rendimiento(solo_riesgo=False) if e['id'] == est.id)
        return (
            hu029['nivel_semaforo'],                                   # HU-029 (lista de riesgo)
            calcular_rendimiento_estudiante(est.id)['nivel_semaforo'], # HU-033 (reporte de proyecto/indicadores)
            semaforo_estudiante(est.id)['nivel'],                      # HU-041
        )

    assert niveles() == ('amarillo', 'amarillo', 'amarillo')

    ParametroSistema.objects.create(clave='umbral_nota_alerta', valor='3.0',
                                    categoria='general', tipo_dato='string')

    assert niveles() == ('verde', 'verde', 'verde')
