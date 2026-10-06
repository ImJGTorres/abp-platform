"""
HU-030 — SCRUM-598: Prueba de regresión.

Repite los escenarios Dado/Cuando/Entonces de HU-030 (alerta por actividad
vencida, alerta por entregable pendiente y marcar como leída) para confirmar
que se mantienen con la ejecución en segundo plano (run_scheduler), y verifica
que el contrato que consume la campanita (AlertasBell.jsx vía alertasApi en
frontend/src/services/docenteApi.js) no cambió: GET /api/alertas/ sigue
exponiendo total_no_leidas y alertas[] con id, tipo, mensaje, estado y
fecha_generacion.
"""
from datetime import date, timedelta

import pytest
from django.core.management import call_command
from django.test import RequestFactory

from apps.alertas.models import Alerta
from apps.alertas.views import AlertaListView, AlertaMarcarLeidaView
from apps.configuracion.models import ParametroSistema
from apps.entregables.models import Entregable
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx
from tests.factories import ActividadFactory, EquipoFactory, MiembroEquipoFactory, UsuarioFactory


@pytest.fixture(autouse=True)
def parametros(db):
    ParametroSistema.objects.get_or_create(  # Equipo.full_clean() lo exige
        clave='max_estudiantes_por_equipo',
        defaults={'valor': '6', 'categoria': 'general', 'tipo_dato': 'integer'})


@pytest.mark.django_db
class TestRegresionAlertaActividadVencida:
    """Dado una actividad vencida, cuando corre el job, entonces se genera la alerta."""

    def test_actividad_vencida_genera_alerta(self):
        estudiante = UsuarioFactory()
        ActividadFactory(
            fecha_limite=date.today() - timedelta(days=1),
            estado='pendiente',
            id_responsable=estudiante,
        )

        call_command('run_scheduler', '--once')

        alerta = Alerta.objects.get(id_usuario_destino=estudiante, tipo='actividad_vencida')
        assert alerta.estado == 'no_leida'


@pytest.mark.django_db
class TestRegresionAlertaEntregablePendiente:
    """Dado un entregable en borrador vencido, cuando corre el job, entonces se genera la alerta."""

    def test_entregable_pendiente_genera_alerta(self):
        estudiante = UsuarioFactory()
        equipo = EquipoFactory()
        MiembroEquipoFactory(equipo=equipo, usuario=estudiante, estado='activo')
        actividad = ActividadFactory(
            fecha_limite=date.today() - timedelta(days=2),
            estado='pendiente',
            id_equipo_asignado=equipo,
        )
        Entregable.objects.create(
            id_actividad=actividad,
            id_equipo=equipo,
            titulo='Entregable test',
            descripcion='desc',
            tipo='documento',
            estado='borrador',
        )

        call_command('run_scheduler', '--once')

        alerta = Alerta.objects.get(id_usuario_destino=estudiante, tipo='entregable_pendiente')
        assert alerta.gravedad == 'media'


@pytest.mark.django_db
class TestRegresionMarcarComoLeida:
    """Dado una alerta no leída, cuando el usuario la marca, entonces queda leída."""

    def setup_method(self):
        self.factory = RequestFactory()

    def test_marcar_alerta_como_leida(self):
        estudiante = UsuarioFactory()
        ActividadFactory(
            fecha_limite=date.today() - timedelta(days=1),
            estado='pendiente',
            id_responsable=estudiante,
        )
        call_command('run_scheduler', '--once')
        alerta = Alerta.objects.get(id_usuario_destino=estudiante)
        assert alerta.estado == 'no_leida'

        req = authenticated_request(
            self.factory, 'PATCH', f'/api/alertas/{alerta.id}/leer/',
            make_payload(user_id=estudiante.id, tipo_rol='estudiante'),
        )
        with auth_ctx(req):
            response = AlertaMarcarLeidaView.as_view()(req, alerta_id=alerta.id)

        assert response.status_code == 200
        alerta.refresh_from_db()
        assert alerta.estado == 'leida'
        assert alerta.fecha_lectura is not None


@pytest.mark.django_db
class TestRegresionCampanitaContadorYLista:
    """La campanita (AlertasBell.jsx) consume total_no_leidas y alertas[] de GET /api/alertas/."""

    def setup_method(self):
        self.factory = RequestFactory()

    def test_get_todas_expone_contador_y_lista_para_la_campanita(self):
        estudiante = UsuarioFactory()
        ActividadFactory(
            fecha_limite=date.today() - timedelta(days=1),
            estado='pendiente',
            id_responsable=estudiante,
        )
        call_command('run_scheduler', '--once')

        req = authenticated_request(
            self.factory, 'GET', '/api/alertas/',
            make_payload(user_id=estudiante.id, tipo_rol='estudiante'),
            query_params={'estado': 'todas'},
        )
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200
        data = response.data
        assert data['total_no_leidas'] == 1
        alerta = data['alertas'][0]
        for campo in ('id', 'tipo', 'mensaje', 'estado', 'fecha_generacion'):
            assert campo in alerta
