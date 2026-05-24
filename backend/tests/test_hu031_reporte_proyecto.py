"""
HU-031 — Reporte completo por proyecto.
"""
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from apps.reportes.views import ReporteProyectoView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


def _reporte_proyecto_base(proyecto_id=1):
    return {
        'proyecto': {'id': proyecto_id, 'nombre': 'ABP', 'estado': 'planificado', 'curso': 'IS I'},
        'objetivos': [{'id': 1, 'descripcion': 'Obj 1', 'tipo': 'general', 'orden': 1}],
        'resultados_aprendizaje': [],
        'hitos': [],
        'progreso_global': {
            'porcentaje_progreso': 50, 'total_fases': 2, 'fases_completadas': 1,
            'total_actividades': 4, 'actividades_completadas': 2,
        },
        'progreso_por_fase': [],
        'resumen_entregables': {
            'total_entregables': 2, 'aprobados': 1, 'rechazados': 0,
            'enviados': 1, 'pendientes': 0, 'tasa_entrega_tiempo_pct': 100.0,
        },
        'equipos': [],
        'avance_por_estudiante': [],
        'estudiantes_bajo_rendimiento': [],
        'umbral_bajo_rendimiento': 3.0,
    }


class TestReporteProyectoView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.services.reporte_proyecto')
    def test_director_obtiene_reporte_con_estructura_completa(self, mock_srv):
        mock_srv.return_value = _reporte_proyecto_base(1)

        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/1/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=1)

        assert response.status_code == 200
        for campo in ('proyecto', 'progreso_global', 'resumen_entregables',
                      'equipos', 'avance_por_estudiante'):
            assert campo in response.data, f"Falta campo: {campo}"

    @patch('apps.reportes.services.reporte_proyecto')
    def test_docente_puede_acceder_al_reporte_proyecto(self, mock_srv):
        mock_srv.return_value = _reporte_proyecto_base(1)

        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/1/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=1)

        assert response.status_code == 200

    @patch('apps.reportes.services.reporte_proyecto')
    def test_proyecto_sin_actividades_retorna_listas_vacias(self, mock_srv):
        data = _reporte_proyecto_base(2)
        data['avance_por_estudiante'] = []
        data['equipos'] = []
        data['progreso_por_fase'] = []
        mock_srv.return_value = data

        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/2/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=2)

        assert response.status_code == 200
        assert response.data['avance_por_estudiante'] == []
        assert response.data['equipos'] == []

    @patch('apps.reportes.services.reporte_proyecto')
    def test_proyecto_inexistente_retorna_404(self, mock_srv):
        mock_srv.return_value = None

        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/999/',
                                    make_payload(tipo_rol='director'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=999)

        assert response.status_code == 404

    def test_estudiante_no_puede_acceder(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/1/',
                                    make_payload(tipo_rol='estudiante'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=1)

        assert response.status_code == 403

    def test_lider_equipo_no_puede_acceder(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/proyecto/1/',
                                    make_payload(tipo_rol='lider_equipo'))
        with auth_ctx(req):
            response = ReporteProyectoView.as_view()(req, proyecto_id=1)

        assert response.status_code == 403
