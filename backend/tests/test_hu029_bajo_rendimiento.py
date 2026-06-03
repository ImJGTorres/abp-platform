"""
HU-029 — Identificar estudiantes con bajo rendimiento.
"""
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from apps.reportes.views import BajoRendimientoView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


def _make_indicadores(nota=2.5, pct_incumplidas=60.0, rechazados=3, en_riesgo=True):
    return {
        'nota_promedio': nota,
        'porcentaje_actividades_incumplidas': pct_incumplidas,
        'actividades_incumplidas': 3,
        'total_actividades': 5,
        'entregables_rechazados': rechazados,
        'total_entregables': 4,
        'en_riesgo': en_riesgo,
        'alertas': ['Nota baja'] if en_riesgo else [],
    }


class TestBajoRendimientoView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.views.get_estudiantes_bajo_rendimiento')
    def test_director_obtiene_lista_estudiantes_en_riesgo(self, mock_srv):
        mock_srv.return_value = [{'id': 5, 'nombre': 'Juan', **_make_indicadores(en_riesgo=True)}]

        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 200
        assert response.data['total'] == 1
        assert 'estudiantes' in response.data

    @patch('apps.reportes.views.get_estudiantes_bajo_rendimiento')
    def test_docente_tiene_acceso_a_bajo_rendimiento(self, mock_srv):
        mock_srv.return_value = []

        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 200

    @patch('apps.reportes.views.get_estudiantes_bajo_rendimiento')
    def test_lista_retorna_total_cero_con_filtro_curso_vacio(self, mock_srv):
        mock_srv.return_value = []

        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'curso_id': '1'})
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 200
        assert response.data['total'] == 0

    @patch('apps.reportes.views.get_estudiantes_bajo_rendimiento')
    def test_periodo_sin_datos_retorna_lista_vacia(self, mock_srv):
        mock_srv.return_value = []

        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'periodo_id': '999'})
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 200
        assert response.data['estudiantes'] == []

    def test_estudiante_no_tiene_acceso(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='estudiante'))
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 403

    def test_lider_equipo_no_tiene_acceso(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='lider_equipo'))
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 403

    def test_curso_id_no_entero_retorna_400(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/bajo-rendimiento/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'curso_id': 'abc'})
        with auth_ctx(req):
            response = BajoRendimientoView.as_view()(req)

        assert response.status_code == 400
