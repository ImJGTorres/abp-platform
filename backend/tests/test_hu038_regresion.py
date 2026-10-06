"""
HU-038 — Pruebas de regresión de pendientes priorizados (SCRUM-514).

Complementa test_hu038_pendientes.py (Gabriel) con lo que pide la tarjeta y
no estaba cubierto:
  - un estudiante no ve pendientes de un equipo del que no es miembro;
  - un líder de equipo no ve pendientes de otro equipo;
  - el endpoint GET /api/dashboard/pendientes/ queda bien conectado para
    docente, líder y director (Gabriel solo lo probó para estudiante);
  - el orden por urgencia desc y fecha asc se cumple también cuando hay
    varios pendientes del mismo tipo o de tipos distintos mezclados.
"""
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from apps.alertas.models import Alerta
from apps.configuracion.models import ParametroSistema
from apps.entregables.models import Entregable
from apps.reportes.pendientes import pendientes_usuario
from apps.usuarios.models import Usuario
from tests.factories import (
    ActividadFactory, EquipoFactory, FaseProyectoFactory, MiembroEquipoFactory, UsuarioFactory,
)

URL = '/api/dashboard/pendientes/'
HOY = date.today()


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def fase():
    return FaseProyectoFactory()


def _actividad(fase, dias, **kw):
    return ActividadFactory(id_fase=fase, fecha_limite=HOY + timedelta(days=dias), estado='pendiente', **kw)


def _cliente(usuario):
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


# ── Aislamiento por rol ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_estudiante_no_ve_actividades_de_un_equipo_del_que_no_es_miembro(fase):
    est = UsuarioFactory()
    otro_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    _actividad(fase, -1, id_equipo_asignado=otro_equipo, nombre='Ajena')

    assert pendientes_usuario(est)['al_dia'] is True


@pytest.mark.django_db
def test_estudiante_no_ve_entregables_de_otro_equipo(fase):
    est = UsuarioFactory()
    mi_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    otro_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=mi_equipo, usuario=est, estado='activo')
    act_otro = _actividad(fase, -1, id_equipo_asignado=otro_equipo)
    Entregable.objects.create(id_actividad=act_otro, id_equipo=otro_equipo, titulo='Ajeno',
                              descripcion='x', tipo='documento', estado='rechazado')

    r = pendientes_usuario(est)
    assert r['al_dia'] is True
    assert r['pendientes'] == []


@pytest.mark.django_db
def test_lider_no_ve_pendientes_de_otro_equipo(fase):
    lider = UsuarioFactory(tipo_rol=Usuario.TipoRol.LIDER_EQUIPO)
    mi_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    otro_equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=mi_equipo, usuario=lider, estado='activo')
    _actividad(fase, -1, id_equipo_asignado=otro_equipo, nombre='De otro equipo')
    propia = _actividad(fase, -1, id_equipo_asignado=mi_equipo, nombre='De mi equipo')

    r = pendientes_usuario(lider)
    assert len(r['pendientes']) == 1
    assert propia.nombre in r['pendientes'][0]['titulo']


@pytest.mark.django_db
def test_miembro_retirado_del_equipo_no_ve_sus_pendientes(fase):
    """Si el estudiante salió del equipo (estado retirado), no debe ver sus actividades."""
    est = UsuarioFactory()
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=equipo, usuario=est, estado='retirado')
    _actividad(fase, -1, id_equipo_asignado=equipo)

    assert pendientes_usuario(est)['al_dia'] is True


# ── Endpoint conectado para todos los roles ────────────────────────────────

@pytest.mark.django_db
def test_endpoint_docente_ve_entregables_sin_calificar(fase):
    docente = fase.id_proyecto.id_curso.id_docente
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    act = _actividad(fase, -1)
    Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Sin nota',
                              descripcion='x', tipo='documento', estado='enviado')

    r = _cliente(docente).get(URL)
    assert r.status_code == 200
    assert r.data['al_dia'] is False
    assert r.data['resumen']['sin_calificar'] == 1


@pytest.mark.django_db
def test_endpoint_lider_ve_alertas_no_leidas(fase):
    lider = UsuarioFactory(tipo_rol=Usuario.TipoRol.LIDER_EQUIPO)
    Alerta.objects.create(tipo='actividad_vencida', id_usuario_destino=lider, mensaje='Atención')

    r = _cliente(lider).get(URL)
    assert r.status_code == 200
    assert r.data['resumen'] == {'total': 1, 'vencido': 0, 'proximo': 0, 'sin_calificar': 0, 'alerta': 1}


@pytest.mark.django_db
def test_endpoint_director_sin_pendientes_esta_al_dia():
    director = UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)
    r = _cliente(director).get(URL)
    assert r.status_code == 200
    assert r.data['al_dia'] is True


@pytest.mark.django_db
def test_endpoint_administrador_ve_sus_propias_alertas():
    admin = UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR)
    Alerta.objects.create(tipo='bajo_rendimiento', id_usuario_destino=admin, mensaje='Revisar')

    r = _cliente(admin).get(URL)
    assert r.status_code == 200
    assert r.data['resumen']['alerta'] == 1


# ── Orden: urgencia desc, fecha asc ─────────────────────────────────────────

@pytest.mark.django_db
def test_varios_vencidos_se_ordenan_por_fecha_mas_antigua_primero(fase):
    est = UsuarioFactory()
    reciente = _actividad(fase, -1, id_responsable=est, nombre='Vencida reciente')
    antigua = _actividad(fase, -5, id_responsable=est, nombre='Vencida antigua')

    r = pendientes_usuario(est)
    titulos = [p['titulo'] for p in r['pendientes']]
    assert titulos == [f'Actividad vencida: {antigua.nombre}', f'Actividad vencida: {reciente.nombre}']


@pytest.mark.django_db
def test_mezcla_de_tipos_respeta_la_urgencia_sobre_la_fecha(fase):
    """Una alerta (urgencia 1) con fecha muy antigua no debe adelantar a un vencido (urgencia 3)."""
    est = UsuarioFactory()
    vencida = _actividad(fase, -1, id_responsable=est)
    Alerta.objects.create(tipo='actividad_vencida', id_usuario_destino=est, mensaje='Vieja',
                          id_proyecto=fase.id_proyecto)

    r = pendientes_usuario(est)
    assert [p['tipo'] for p in r['pendientes']] == ['vencido', 'alerta']
    assert vencida.nombre in r['pendientes'][0]['titulo']


@pytest.mark.django_db
def test_director_ve_rojos_y_alertas_juntos_en_orden(fase, monkeypatch):
    director = UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)
    Alerta.objects.create(tipo='bajo_rendimiento', id_usuario_destino=director, mensaje='Aviso general')
    monkeypatch.setattr(
        'apps.reportes.services.get_estudiantes_bajo_rendimiento', lambda **kw: [{}, {}]
    )

    r = pendientes_usuario(director)
    # Ambos quedan con tipo 'alerta', pero el resumen de rojos (urgencia 2) va
    # primero que la alerta de Alerta.objects (urgencia 1).
    assert [p['urgencia'] for p in r['pendientes']] == [2, 1]
    assert r['pendientes'][0]['titulo'] == '2 estudiante(s) en rojo (riesgo crítico)'
    assert r['pendientes'][1]['titulo'] == 'Aviso general'
    assert r['resumen']['alerta'] == 2
