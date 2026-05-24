"""
HU-033 — Dashboard de indicadores institucionales.
"""
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from apps.reportes.views import IndicadoresDashboardView, IndicadoresTendenciaView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


def _indicadores_base():
    return {
        'filtros_aplicados': {'periodo_id': 1, 'curso_id': None},
        'resumen_periodo': {
            'periodo_id': 1, 'periodo_nombre': '2026-1', 'periodo_estado': 'activo',
            'total_cursos': 3, 'cursos_activos': 2, 'total_estudiantes': 45,
            'total_proyectos': 6, 'proyectos_activos': 6,
            'avance_promedio_proyectos_pct': 38.5, 'tasa_aprobacion_pct': 82.0,
        },
        'distribucion_notas': {
            'rango_0_2': 4, 'rango_2_3': 8, 'rango_3_4': 20, 'rango_4_5': 13,
            'nota_promedio_global': 3.42,
        },
        'proyectos': [],
        'docentes_activos': [],
        'estudiantes_riesgo_por_curso': [],
    }


class TestIndicadoresDashboardView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.services.indicadores_dashboard')
    def test_director_obtiene_indicadores_con_estructura_completa(self, mock_srv):
        mock_srv.return_value = _indicadores_base()

        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'periodo_id': '1'})
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 200
        for campo in ('resumen_periodo', 'distribucion_notas', 'proyectos',
                      'docentes_activos', 'estudiantes_riesgo_por_curso'):
            assert campo in response.data, f"Falta campo: {campo}"

    @patch('apps.reportes.services.indicadores_dashboard')
    def test_administrador_puede_acceder_a_indicadores(self, mock_srv):
        mock_srv.return_value = _indicadores_base()

        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='administrador'))
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 200

    @patch('apps.reportes.services.indicadores_dashboard')
    def test_periodo_vacio_retorna_proyectos_lista_vacia(self, mock_srv):
        data = _indicadores_base()
        data['resumen_periodo'] = {
            'periodo_id': 99, 'total_cursos': 0, 'total_estudiantes': 0,
            'total_proyectos': 0, 'avance_promedio_proyectos_pct': 0,
            'tasa_aprobacion_pct': 0,
        }
        data['proyectos'] = []
        mock_srv.return_value = data

        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'periodo_id': '99'})
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 200
        assert response.data['proyectos'] == []

    def test_docente_no_puede_acceder_a_indicadores(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 403

    def test_estudiante_no_puede_acceder_a_indicadores(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='estudiante'))
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 403

    def test_lider_equipo_no_puede_acceder_a_indicadores(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='lider_equipo'))
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 403

    def test_periodo_id_no_entero_retorna_400(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/',
                                    make_payload(tipo_rol='director'),
                                    query_params={'periodo_id': 'abc'})
        with auth_ctx(req):
            response = IndicadoresDashboardView.as_view()(req)

        assert response.status_code == 400

    @patch('apps.reportes.services.indicadores_tendencia')
    def test_tendencia_retorna_periodos_en_orden_cronologico(self, mock_srv):
        mock_srv.return_value = {
            'n_periodos': 2,
            'periodos': [
                {'periodo_id': 1, 'avance_promedio_proyectos_pct': 50.0},
                {'periodo_id': 2, 'avance_promedio_proyectos_pct': 65.0},
            ],
            'tendencias': {'avance_proyectos': 15.0},
        }

        req = authenticated_request(self.factory, 'GET', '/api/reportes/indicadores/tendencia/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = IndicadoresTendenciaView.as_view()(req)

        assert response.status_code == 200
        assert 'periodos' in response.data
        assert 'tendencias' in response.data
        assert len(response.data['periodos']) == 2
