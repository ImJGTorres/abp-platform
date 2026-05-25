"""
HU-034 — Exportar reportes en PDF y Excel.
"""
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from apps.exportaciones.views import SolicitarExportacionView, EstadoExportacionView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


class TestSolicitarExportacionView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.exportaciones.views.generar_exportacion')
    @patch('apps.exportaciones.models.Exportacion.objects.create')
    def test_solicitar_pdf_retorna_201_con_id_y_estado(self, mock_create, mock_gen):
        mock_exp = MagicMock()
        mock_exp.id = 42
        mock_exp.estado = 'listo'
        mock_exp.mensaje_error = None
        mock_create.return_value = mock_exp

        req = authenticated_request(
            self.factory, 'POST', '/api/exportar/reporte/',
            make_payload(tipo_rol='director'),
            data={'tipo_reporte': 'proyecto', 'formato': 'pdf',
                  'parametros': {'proyecto_id': 1}},
        )
        with auth_ctx(req):
            response = SolicitarExportacionView.as_view()(req)

        assert response.status_code == 201
        assert 'id' in response.data
        assert 'estado' in response.data

    @patch('apps.exportaciones.views.generar_exportacion')
    @patch('apps.exportaciones.models.Exportacion.objects.create')
    def test_solicitar_excel_retorna_201(self, mock_create, mock_gen):
        mock_exp = MagicMock()
        mock_exp.id = 43
        mock_exp.estado = 'listo'
        mock_exp.mensaje_error = None
        mock_create.return_value = mock_exp

        req = authenticated_request(
            self.factory, 'POST', '/api/exportar/reporte/',
            make_payload(tipo_rol='director'),
            data={'tipo_reporte': 'proyecto', 'formato': 'excel',
                  'parametros': {'proyecto_id': 1}},
        )
        with auth_ctx(req):
            response = SolicitarExportacionView.as_view()(req)

        assert response.status_code == 201

    @patch('apps.exportaciones.models.Exportacion.objects.create')
    def test_formato_no_permitido_retorna_400_sin_crear_registro(self, mock_create):
        req = authenticated_request(
            self.factory, 'POST', '/api/exportar/reporte/',
            make_payload(tipo_rol='director'),
            data={'tipo_reporte': 'proyecto', 'formato': 'word',
                  'parametros': {'proyecto_id': 1}},
        )
        with auth_ctx(req):
            response = SolicitarExportacionView.as_view()(req)

        assert response.status_code == 400
        mock_create.assert_not_called()

    @patch('apps.exportaciones.models.Exportacion.objects.create')
    def test_tipo_reporte_desconocido_retorna_400(self, mock_create):
        req = authenticated_request(
            self.factory, 'POST', '/api/exportar/reporte/',
            make_payload(tipo_rol='director'),
            data={'tipo_reporte': 'desconocido', 'formato': 'pdf', 'parametros': {}},
        )
        with auth_ctx(req):
            response = SolicitarExportacionView.as_view()(req)

        assert response.status_code == 400

    @patch('apps.exportaciones.models.Exportacion.objects.create')
    def test_falta_proyecto_id_para_tipo_proyecto_retorna_400(self, mock_create):
        req = authenticated_request(
            self.factory, 'POST', '/api/exportar/reporte/',
            make_payload(tipo_rol='director'),
            data={'tipo_reporte': 'proyecto', 'formato': 'pdf', 'parametros': {}},
        )
        with auth_ctx(req):
            response = SolicitarExportacionView.as_view()(req)

        assert response.status_code == 400


class TestEstadoExportacionView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.exportaciones.models.Exportacion.objects.get')
    def test_exportacion_lista_incluye_url_descarga(self, mock_get):
        mock_exp = MagicMock()
        mock_exp.id = 1
        mock_exp.tipo_reporte = 'proyecto'
        mock_exp.formato = 'pdf'
        mock_exp.estado = 'listo'
        mock_exp.ruta_archivo = '/fake/media/exportaciones/abc.pdf'
        mock_exp.fecha_solicitud.isoformat.return_value = '2026-05-01T00:00:00'
        mock_exp.fecha_disponible.isoformat.return_value = '2026-05-01T00:01:00'
        mock_exp.mensaje_error = None
        mock_get.return_value = mock_exp

        req = authenticated_request(self.factory, 'GET', '/api/exportar/1/estado/',
                                    make_payload(user_id=1, tipo_rol='director'))
        with auth_ctx(req), patch('apps.exportaciones.views.os.path.relpath',
                                  return_value='exportaciones/abc.pdf'):
            response = EstadoExportacionView.as_view()(req, exportacion_id=1)

        assert response.status_code == 200
        assert response.data['estado'] == 'listo'
        assert response.data['url_descarga'] is not None

    @patch('apps.exportaciones.models.Exportacion.objects.get')
    def test_exportacion_generando_no_tiene_url_descarga(self, mock_get):
        mock_exp = MagicMock()
        mock_exp.id = 2
        mock_exp.tipo_reporte = 'proyecto'
        mock_exp.formato = 'pdf'
        mock_exp.estado = 'generando'
        mock_exp.ruta_archivo = None
        mock_exp.fecha_solicitud.isoformat.return_value = '2026-05-01T00:00:00'
        mock_exp.fecha_disponible = None
        mock_exp.mensaje_error = None
        mock_get.return_value = mock_exp

        req = authenticated_request(self.factory, 'GET', '/api/exportar/2/estado/',
                                    make_payload(user_id=1, tipo_rol='director'))
        with auth_ctx(req):
            response = EstadoExportacionView.as_view()(req, exportacion_id=2)

        assert response.status_code == 200
        assert response.data['url_descarga'] is None

    @patch('apps.exportaciones.models.Exportacion.objects.get')
    def test_exportacion_en_error_incluye_mensaje_error(self, mock_get):
        """Estado error → url_descarga nula y mensaje_error presente en respuesta."""
        mock_exp = MagicMock()
        mock_exp.id = 3
        mock_exp.tipo_reporte = 'proyecto'
        mock_exp.formato = 'pdf'
        mock_exp.estado = 'error'
        mock_exp.ruta_archivo = None
        mock_exp.fecha_solicitud.isoformat.return_value = '2026-05-01T00:00:00'
        mock_exp.fecha_disponible = None
        mock_exp.mensaje_error = 'Proyecto no encontrado al generar PDF'
        mock_get.return_value = mock_exp

        req = authenticated_request(self.factory, 'GET', '/api/exportar/3/estado/',
                                    make_payload(user_id=1, tipo_rol='director'))
        with auth_ctx(req):
            response = EstadoExportacionView.as_view()(req, exportacion_id=3)

        assert response.status_code == 200
        assert response.data['estado'] == 'error'
        assert response.data['url_descarga'] is None
        assert response.data['mensaje_error'] == 'Proyecto no encontrado al generar PDF'

    @patch('apps.exportaciones.models.Exportacion.objects.get')
    def test_exportacion_de_otro_usuario_retorna_404(self, mock_get):
        from apps.exportaciones.models import Exportacion
        mock_get.side_effect = Exportacion.DoesNotExist

        req = authenticated_request(self.factory, 'GET', '/api/exportar/99/estado/',
                                    make_payload(user_id=1, tipo_rol='director'))
        with auth_ctx(req):
            response = EstadoExportacionView.as_view()(req, exportacion_id=99)

        assert response.status_code == 404
