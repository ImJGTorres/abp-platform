"""
HU-038 — Endpoint GET /api/dashboard/pendientes/ (SCRUM-509).
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.alertas.models import Alerta
from apps.configuracion.models import ParametroSistema
from apps.entregables.models import Entregable
from apps.evaluacion.models import Evaluacion, Rubrica
from apps.reportes.pendientes import pendientes_usuario
from apps.usuarios.models import Usuario
from tests.factories import (ActividadFactory, DocenteFactory, EquipoFactory, FaseProyectoFactory,
                             MiembroEquipoFactory, UsuarioFactory)

URL = '/api/dashboard/pendientes/'
HOY = date.today()


@pytest.fixture(autouse=True)
def parametros(db):
    # Equipo.full_clean() exige este parámetro
    ParametroSistema.objects.get_or_create(
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.fixture
def fase():
    return FaseProyectoFactory()


def _actividad(fase, dias, **kw):
    return ActividadFactory(id_fase=fase, fecha_limite=HOY + timedelta(days=dias), estado='pendiente', **kw)


@pytest.mark.django_db
def test_estudiante_vencida_sale_antes_que_proxima(fase):
    est = UsuarioFactory()
    proxima = _actividad(fase, 2, id_responsable=est, nombre='Próxima')
    vencida = _actividad(fase, -1, id_responsable=est, nombre='Vencida')
    _actividad(fase, 10, id_responsable=est)                            # lejana: no es pendiente
    ActividadFactory(id_fase=fase, id_responsable=est, fecha_limite=HOY - timedelta(days=3),
                     estado='completada')                               # completada: no es pendiente

    r = pendientes_usuario(est)

    assert r['al_dia'] is False
    assert [(p['tipo'], p['urgencia']) for p in r['pendientes']] == [('vencido', 3), ('proximo', 2)]
    assert vencida.nombre in r['pendientes'][0]['titulo']
    assert proxima.nombre in r['pendientes'][1]['titulo']
    assert r['pendientes'][0]['enlace'] == f'/estudiante/proyectos/{fase.id_proyecto_id}/actividades'
    assert r['resumen'] == {'total': 2, 'vencido': 1, 'proximo': 1, 'sin_calificar': 0, 'alerta': 0}


@pytest.mark.django_db
def test_usuario_sin_pendientes_esta_al_dia():
    r = pendientes_usuario(UsuarioFactory())
    assert r['al_dia'] is True
    assert r['pendientes'] == []
    assert r['resumen']['total'] == 0


@pytest.mark.django_db
def test_lider_ve_actividades_del_equipo_entregables_y_alertas(fase):
    lider = UsuarioFactory(tipo_rol=Usuario.TipoRol.LIDER_EQUIPO)
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    MiembroEquipoFactory(equipo=equipo, usuario=lider, estado='activo')
    act = _actividad(fase, -2, id_equipo_asignado=equipo)
    Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Informe', descripcion='x',
                              tipo='documento', estado='rechazado')
    Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Aprobado', descripcion='x',
                              tipo='documento', estado='aprobado')
    Alerta.objects.create(tipo='actividad_vencida', id_usuario_destino=lider, mensaje='Ojo',
                          id_proyecto=fase.id_proyecto)
    Alerta.objects.create(tipo='actividad_vencida', id_usuario_destino=lider, mensaje='Leída',
                          estado='leida')

    r = pendientes_usuario(lider)

    assert [p['tipo'] for p in r['pendientes']] == ['vencido', 'proximo', 'alerta']
    assert r['pendientes'][1]['titulo'] == 'Entregable por corregir: Informe'
    assert r['pendientes'][1]['enlace'].endswith(f'/actividades/{act.id}/entregables')
    assert r['pendientes'][2]['enlace'] == f'/estudiante/proyectos/{fase.id_proyecto_id}'


@pytest.mark.django_db
def test_docente_sin_calificar_excluye_evaluados_y_ve_vencidas(fase):
    docente = fase.id_proyecto.id_curso.id_docente
    equipo = EquipoFactory(proyecto=fase.id_proyecto)
    act = _actividad(fase, -1)
    pendiente = Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Sin nota',
                                          descripcion='x', tipo='documento', estado='enviado')
    calificado = Entregable.objects.create(id_actividad=act, id_equipo=equipo, titulo='Con nota',
                                           descripcion='x', tipo='documento', estado='enviado')
    rubrica = Rubrica.objects.create(nombre='R', id_docente=docente)
    Evaluacion.objects.create(id_entregable=calificado, id_rubrica=rubrica, id_docente=docente,
                              estado='publicada')

    r = pendientes_usuario(docente)

    assert [(p['tipo'], p['urgencia']) for p in r['pendientes']] == [('sin_calificar', 3), ('vencido', 2)]
    assert pendiente.titulo in r['pendientes'][0]['titulo']
    assert r['pendientes'][0]['enlace'] == (f'/docente/proyectos/{fase.id_proyecto_id}/fases/{fase.id}'
                                            f'/actividades/{act.id}/entregables')
    # Otro docente no ve los pendientes de este curso
    assert pendientes_usuario(DocenteFactory())['al_dia'] is True


@pytest.mark.django_db
@patch('apps.reportes.services.get_estudiantes_bajo_rendimiento', return_value=[{}, {}, {}])
def test_director_ve_resumen_de_estudiantes_en_rojo(mock_rojos):
    director = UsuarioFactory(tipo_rol=Usuario.TipoRol.DIRECTOR)
    r = pendientes_usuario(director)
    assert r['pendientes'] == [{'tipo': 'alerta', 'titulo': '3 estudiante(s) en rojo (riesgo crítico)',
                                'fecha': HOY, 'urgencia': 2, 'enlace': '/director/riesgo'}]
    assert mock_rojos.call_args.kwargs['solo_riesgo'] is True


@pytest.mark.django_db
@patch('apps.reportes.services.get_estudiantes_bajo_rendimiento', return_value=[])
def test_administrador_sin_rojos_ni_alertas_esta_al_dia(mock_rojos):
    assert pendientes_usuario(UsuarioFactory(tipo_rol=Usuario.TipoRol.ADMINISTRADOR))['al_dia'] is True


@pytest.mark.django_db
def test_endpoint_responde_al_usuario_autenticado(fase):
    est = UsuarioFactory()
    _actividad(fase, -1, id_responsable=est)
    cliente = APIClient()
    cliente.force_authenticate(user=est)

    r = cliente.get(URL)

    assert r.status_code == 200
    assert r.data['al_dia'] is False
    assert r.json()['pendientes'][0]['fecha'] == str(HOY - timedelta(days=1))


@pytest.mark.django_db
def test_endpoint_sin_autenticar_retorna_401():
    assert APIClient().get(URL).status_code == 401
