"""
HU-030 — SCRUM-597: Pruebas del job en segundo plano (run_scheduler).

Complementa los mocks de test_hu030_scheduler.py y test_hu030_alertas.py con
pruebas de integración (base de datos real vía factories) que verifican los
criterios de "Listo cuando" de la subtarea:

- call_command("run_scheduler", "--once") genera alertas sin ninguna petición HTTP.
- GET /api/alertas/ ya no crea alertas (SCRUM-595).
- Gravedad correcta por tipo; ejecutar dos veces no duplica alertas ni cola_correo.
- Intervalo: una tarea no se repite antes de 15 minutos y sí después.
- Aceptación: actividad vencida sin que nadie entre a la plataforma, el job la
  genera y aparece luego en la campanita (GET /api/alertas/).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.test import RequestFactory

from apps.alertas.management.commands import run_scheduler
from apps.alertas.models import Alerta, ColaCorreo
from apps.alertas.views import AlertaListView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx
from tests.factories import ActividadFactory, UsuarioFactory


def _crear_actividad_vencida(responsable):
    return ActividadFactory(
        fecha_limite=date.today() - timedelta(days=1),
        estado='pendiente',
        id_responsable=responsable,
    )


@pytest.mark.django_db
class TestRunSchedulerGeneraAlertasSinHttp:

    def test_once_genera_alertas_sin_ninguna_peticion_http(self):
        estudiante = UsuarioFactory()
        _crear_actividad_vencida(estudiante)

        assert Alerta.objects.filter(id_usuario_destino=estudiante).count() == 0

        call_command('run_scheduler', '--once')

        alertas = Alerta.objects.filter(id_usuario_destino=estudiante)
        assert alertas.count() == 1
        assert alertas.first().tipo == 'actividad_vencida'

    def test_gravedad_correcta_para_actividad_vencida(self):
        estudiante = UsuarioFactory()
        _crear_actividad_vencida(estudiante)

        call_command('run_scheduler', '--once')

        alerta = Alerta.objects.get(id_usuario_destino=estudiante)
        assert alerta.gravedad == 'alta'

    def test_ejecutar_dos_veces_no_duplica_alertas_ni_cola_correo(self):
        estudiante = UsuarioFactory()
        _crear_actividad_vencida(estudiante)

        call_command('run_scheduler', '--once')
        total_alertas_1 = Alerta.objects.filter(id_usuario_destino=estudiante).count()
        total_correos_1 = ColaCorreo.objects.filter(id_usuario_destino=estudiante).count()

        call_command('run_scheduler', '--once')
        total_alertas_2 = Alerta.objects.filter(id_usuario_destino=estudiante).count()
        total_correos_2 = ColaCorreo.objects.filter(id_usuario_destino=estudiante).count()

        assert total_alertas_1 == total_alertas_2 == 1
        assert total_correos_1 == total_correos_2 == 1


@pytest.mark.django_db
class TestGetAlertasNoGeneraConDatosReales:

    def setup_method(self):
        self.factory = RequestFactory()

    def test_get_no_crea_alertas_aunque_haya_actividades_vencidas(self):
        """SCRUM-595: GET /api/alertas/ solo lee; el job es quien genera."""
        estudiante = UsuarioFactory()
        _crear_actividad_vencida(estudiante)

        req = authenticated_request(
            self.factory, 'GET', '/api/alertas/',
            make_payload(user_id=estudiante.id, tipo_rol='estudiante'),
        )
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200
        assert Alerta.objects.filter(id_usuario_destino=estudiante).count() == 0


class TestIntervaloDeEjecucion:

    def test_tarea_alertas_no_se_repite_antes_de_15_minutos_y_si_despues(self):
        """RNF27 / SCRUM-594: intervalo real de 15 min, con tiempo simulado."""
        tarea_alertas = MagicMock()
        tareas_parcheadas = [('alertas', tarea_alertas, 15)]
        ultima = {}

        with patch.object(run_scheduler, 'TAREAS', tareas_parcheadas):
            run_scheduler.correr_tareas(ultima, ahora=0)
            run_scheduler.correr_tareas(ultima, ahora=14 * 60)   # 14 min: no se repite
            run_scheduler.correr_tareas(ultima, ahora=15 * 60)   # 15 min: sí se repite

        assert tarea_alertas.call_count == 2


@pytest.mark.django_db
class TestAceptacionAlertaSinSesionAbierta:
    """
    Escenario de aceptación de SCRUM-597: se crea una actividad vencida sin que
    ningún usuario consulte la plataforma; el job en segundo plano
    (run_scheduler --once) la detecta y, al revisar después la campanita
    (GET /api/alertas/), la alerta ya está disponible.
    """

    def setup_method(self):
        self.factory = RequestFactory()

    def test_actividad_vencida_aparece_en_campanita_sin_que_nadie_entre(self):
        estudiante = UsuarioFactory()
        _crear_actividad_vencida(estudiante)

        # Nadie entra a la plataforma: solo corre el job en segundo plano.
        call_command('run_scheduler', '--once')

        req = authenticated_request(
            self.factory, 'GET', '/api/alertas/',
            make_payload(user_id=estudiante.id, tipo_rol='estudiante'),
        )
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200
        data = response.data
        assert data['total_no_leidas'] == 1
        assert data['alertas'][0]['tipo'] == 'actividad_vencida'
