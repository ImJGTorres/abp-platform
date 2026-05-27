"""
HU-032 — Reporte por estudiante y cálculo de nota ponderada.
"""
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from apps.reportes.views import ReporteEstudianteProyectoView
from tests.conftest_hu import make_payload, authenticated_request, auth_ctx


class TestCalcularNotaPonderada:

    @patch('apps.reportes.services._peso')
    def test_pesos_70_15_15_calcula_nota_correctamente(self, mock_peso):
        mock_peso.side_effect = lambda clave, default: {
            'peso_evaluacion_docente': 0.70,
            'peso_autoevaluacion': 0.15,
            'peso_coevaluacion': 0.15,
        }[clave]

        from apps.reportes.services import calcular_nota_ponderada
        result = calcular_nota_ponderada(nota_docente_5=4.0, nota_auto_5=3.0, nota_co_5=3.5)

        # 4.0*0.70 + 3.0*0.15 + 3.5*0.15 = 2.8 + 0.45 + 0.525 = 3.775
        assert abs(result['nota_final'] - 3.78) < 0.05
        assert 'docente' in result['componentes']
        assert 'autoevaluacion' in result['componentes']

    @patch('apps.reportes.services._peso', side_effect=lambda c, d: d)
    def test_sin_auto_ni_co_todo_el_peso_va_al_docente(self, mock_peso):
        from apps.reportes.services import calcular_nota_ponderada

        result = calcular_nota_ponderada(nota_docente_5=3.5, nota_auto_5=None, nota_co_5=None)

        assert result['nota_final'] == 3.5
        assert 'autoevaluacion' not in result['componentes']
        assert 'coevaluacion' not in result['componentes']
        assert result['componentes']['docente']['peso_aplicado'] == 100.0

    @patch('apps.reportes.services._peso')
    def test_pesos_60_20_20_calcula_nota_correctamente(self, mock_peso):
        mock_peso.side_effect = lambda clave, default: {
            'peso_evaluacion_docente': 0.60,
            'peso_autoevaluacion': 0.20,
            'peso_coevaluacion': 0.20,
        }[clave]

        from apps.reportes.services import calcular_nota_ponderada
        result = calcular_nota_ponderada(nota_docente_5=5.0, nota_auto_5=2.0, nota_co_5=3.0)

        # 5.0*0.60 + 2.0*0.20 + 3.0*0.20 = 3.0 + 0.4 + 0.6 = 4.0
        assert abs(result['nota_final'] - 4.0) < 0.05

    @patch('apps.reportes.services._peso', side_effect=lambda c, d: d)
    def test_nota_docente_cero_retorna_nota_final_cero(self, mock_peso):
        from apps.reportes.services import calcular_nota_ponderada

        result = calcular_nota_ponderada(nota_docente_5=0.0)

        assert result['nota_final'] == 0.0

    @patch('apps.reportes.services._peso', side_effect=lambda c, d: d)
    def test_nota_docente_negativa_retorna_valor_negativo(self, mock_peso):
        """La función no valida el rango — delega esa responsabilidad a la capa superior."""
        from apps.reportes.services import calcular_nota_ponderada

        result = calcular_nota_ponderada(nota_docente_5=-1.0, nota_auto_5=None, nota_co_5=None)

        assert result['nota_final'] == -1.0


class TestReporteEstudianteView:

    def setup_method(self):
        self.factory = RequestFactory()

    @patch('apps.reportes.services.reporte_estudiante_proyecto')
    def test_docente_obtiene_reporte_con_nota_y_desempeno(self, mock_srv):
        mock_srv.return_value = {
            'estudiante': {'id': 5, 'nombre': 'Juan', 'apellido': 'Pérez'},
            'proyecto': {'id': 1, 'nombre': 'ABP'},
            'equipo': {'id': 2, 'nombre': 'Equipo B'},
            'nota_final': {'nota_final': 3.5, 'componentes': {}, 'nota_docente_5': 3.5},
            'desempeno': {},
            'resultados_aprendizaje': [],
            'historial_entregables': [],
            'historial_actividades': [],
        }

        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/5/proyecto/1/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=5, proyecto_id=1)

        assert response.status_code == 200
        assert 'nota_final' in response.data
        assert 'desempeno' in response.data

    @patch('apps.reportes.services.reporte_estudiante_proyecto')
    def test_docente_puede_ver_reporte_de_cualquier_estudiante(self, mock_srv):
        mock_srv.return_value = {
            'estudiante': {'id': 7}, 'proyecto': {}, 'equipo': None,
            'nota_final': {}, 'desempeno': {},
            'resultados_aprendizaje': [], 'historial_entregables': [], 'historial_actividades': [],
        }

        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/7/proyecto/1/',
                                    make_payload(user_id=1, tipo_rol='docente'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=7, proyecto_id=1)

        assert response.status_code == 200

    @patch('apps.reportes.services.reporte_estudiante_proyecto')
    def test_estudiante_puede_ver_su_propio_reporte(self, mock_srv):
        mock_srv.return_value = {
            'estudiante': {'id': 10}, 'proyecto': {}, 'equipo': None,
            'nota_final': {}, 'desempeno': {},
            'resultados_aprendizaje': [], 'historial_entregables': [], 'historial_actividades': [],
        }

        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/10/proyecto/1/',
                                    make_payload(user_id=10, tipo_rol='estudiante'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=10, proyecto_id=1)

        assert response.status_code == 200

    def test_estudiante_no_puede_ver_reporte_de_otro_estudiante(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/5/proyecto/1/',
                                    make_payload(user_id=10, tipo_rol='estudiante'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=5, proyecto_id=1)

        assert response.status_code == 403

    def test_lider_equipo_no_puede_ver_reporte_estudiante(self):
        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/5/proyecto/1/',
                                    make_payload(user_id=1, tipo_rol='lider_equipo'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=5, proyecto_id=1)

        assert response.status_code == 403

    @patch('apps.reportes.services.reporte_estudiante_proyecto')
    def test_estudiante_inexistente_retorna_404(self, mock_srv):
        mock_srv.return_value = None

        req = authenticated_request(self.factory, 'GET', '/api/reportes/estudiante/999/proyecto/1/',
                                    make_payload(tipo_rol='docente'))
        with auth_ctx(req):
            response = ReporteEstudianteProyectoView.as_view()(req, estudiante_id=999, proyecto_id=1)

        assert response.status_code == 404
