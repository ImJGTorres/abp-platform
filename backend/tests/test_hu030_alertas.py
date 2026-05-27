"""
HU-030 — Alertas por retrasos.
"""
from unittest.mock import patch, MagicMock
from django.db import IntegrityError
from django.test import RequestFactory

from apps.alertas.views import AlertaListView, AlertaMarcarLeidaView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


class TestCrearAlerta:
    """Tests de lógica interna de _crear_alerta usando mocks de ORM."""

    @patch('apps.alertas.services.transaction')
    @patch('apps.alertas.models.Alerta.objects.create')
    def test_nueva_alerta_retorna_true(self, mock_create, mock_transaction):
        from apps.alertas.services import _crear_alerta
        mock_create.return_value = MagicMock()

        result = _crear_alerta('actividad_vencida', usuario_id=5,
                               mensaje='Actividad vencida', proyecto_id=1, referencia_id=10)

        assert result is True
        mock_create.assert_called_once()

    @patch('apps.alertas.services.transaction')
    @patch('apps.alertas.models.Alerta.objects.create')
    def test_alerta_duplicada_retorna_false(self, mock_create, mock_transaction):
        """IntegrityError por constraint único → devuelve False sin propagar excepción."""
        from apps.alertas.services import _crear_alerta
        mock_create.side_effect = IntegrityError

        result = _crear_alerta('actividad_vencida', usuario_id=5,
                               mensaje='test', proyecto_id=1, referencia_id=10)

        assert result is False

    @patch('apps.alertas.services.transaction')
    @patch('apps.alertas.models.Alerta.objects.create')
    def test_alerta_sin_proyecto_ni_referencia_retorna_true(self, mock_create, mock_transaction):
        from apps.alertas.services import _crear_alerta
        mock_create.return_value = MagicMock()

        result = _crear_alerta('bajo_rendimiento', usuario_id=3, mensaje='Bajo rendimiento')

        assert result is True
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs.get('id_proyecto_id') is None
        assert call_kwargs.get('referencia_id') is None

    @patch('apps.alertas.services.transaction')
    @patch('apps.alertas.models.Alerta.objects.create')
    def test_crea_alerta_con_tipo_correcto(self, mock_create, mock_transaction):
        from apps.alertas.services import _crear_alerta
        mock_create.return_value = MagicMock()

        _crear_alerta('entregable_pendiente', usuario_id=7, mensaje='Entregable sin entregar',
                      proyecto_id=2, referencia_id=15)

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['tipo'] == 'entregable_pendiente'
        assert call_kwargs['id_usuario_destino_id'] == 7


class TestAlertaListView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.alertas.views.AlertaSerializer')
    @patch('apps.alertas.models.Alerta.objects')
    def test_estudiante_puede_listar_sus_alertas(self, mock_objects, mock_serializer_cls):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.count.return_value = 2
        mock_objects.filter.return_value = mock_qs
        mock_serializer_cls.return_value.data = []

        req = authenticated_request(self.factory, 'GET', '/api/alertas/',
                                    make_payload(tipo_rol='estudiante', user_id=10))
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200

    @patch('apps.alertas.views.AlertaSerializer')
    @patch('apps.alertas.models.Alerta.objects')
    def test_docente_puede_listar_sus_alertas(self, mock_objects, mock_serializer_cls):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_objects.filter.return_value = mock_qs
        mock_serializer_cls.return_value.data = []

        req = authenticated_request(self.factory, 'GET', '/api/alertas/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200

    @patch('apps.alertas.views.AlertaSerializer')
    @patch('apps.alertas.models.Alerta.objects')
    def test_director_puede_listar_sus_alertas(self, mock_objects, mock_serializer_cls):
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_objects.filter.return_value = mock_qs
        mock_serializer_cls.return_value.data = []

        req = authenticated_request(self.factory, 'GET', '/api/alertas/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 200

    def test_estado_invalido_retorna_400(self):
        req = authenticated_request(self.factory, 'GET', '/api/alertas/',
                                    make_payload(tipo_rol='estudiante'),
                                    query_params={'estado': 'invalido'})
        with auth_ctx(req):
            response = AlertaListView.as_view()(req)

        assert response.status_code == 400


class TestAlertaMarcarLeidaView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.alertas.views.AlertaSerializer')
    @patch('apps.alertas.models.Alerta.objects.get')
    def test_alerta_no_leida_cambia_a_leida_y_guarda(self, mock_get, mock_serializer_cls):
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = 'no_leida'
        mock_alerta.id_usuario_destino_id = 10
        mock_get.return_value = mock_alerta
        mock_serializer_cls.return_value.data = {'id': 1, 'estado': 'leida'}

        req = authenticated_request(self.factory, 'PATCH', '/api/alertas/1/leer/',
                                    make_payload(user_id=10, tipo_rol='estudiante'))
        with auth_ctx(req):
            response = AlertaMarcarLeidaView.as_view()(req, alerta_id=1)

        assert response.status_code == 200
        mock_alerta.save.assert_called_once()

    @patch('apps.alertas.views.AlertaSerializer')
    @patch('apps.alertas.models.Alerta.objects.get')
    def test_alerta_ya_leida_retorna_200_sin_guardar(self, mock_get, mock_serializer_cls):
        """Alerta ya marcada como leída no vuelve a llamar .save()."""
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = 'leida'
        mock_alerta.id_usuario_destino_id = 10
        mock_get.return_value = mock_alerta
        mock_serializer_cls.return_value.data = {'id': 1, 'estado': 'leida'}

        req = authenticated_request(self.factory, 'PATCH', '/api/alertas/1/leer/',
                                    make_payload(user_id=10, tipo_rol='estudiante'))
        with auth_ctx(req):
            response = AlertaMarcarLeidaView.as_view()(req, alerta_id=1)

        assert response.status_code == 200
        mock_alerta.save.assert_not_called()

    @patch('apps.alertas.models.Alerta.objects.get')
    def test_alerta_de_otro_usuario_retorna_404(self, mock_get):
        from apps.alertas.models import Alerta
        mock_get.side_effect = Alerta.DoesNotExist

        req = authenticated_request(self.factory, 'PATCH', '/api/alertas/1/leer/',
                                    make_payload(user_id=99, tipo_rol='estudiante'))
        with auth_ctx(req):
            response = AlertaMarcarLeidaView.as_view()(req, alerta_id=1)

        assert response.status_code == 404
