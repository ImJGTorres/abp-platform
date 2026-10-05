"""
HU-029 — Servicio único de semáforo de 3 niveles (RF34).
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.reportes.semaforo import clasificar_semaforo, obtener_umbrales

UMBRALES_DEFECTO = {
    'nota_rojo': Decimal('3.0'),
    'pct_rojo': 50,
    'nota_amarillo': Decimal('3.5'),
    'pct_amarillo': 25,
}


def _sin_parametros(clave, default):
    return default


@patch('apps.reportes.services._get_parametro', side_effect=_sin_parametros)
class TestClasificarSemaforo:

    @pytest.mark.parametrize('nota, pct, esperado', [
        (2.8, 10, 'rojo'),
        (3.2, 10, 'amarillo'),
        (4.0, 10, 'verde'),
        (4.0, 60, 'rojo'),
    ])
    def test_casos_de_referencia(self, _mock, nota, pct, esperado):
        assert clasificar_semaforo(nota, pct) == esperado

    @pytest.mark.parametrize('nota, pct, esperado', [
        (3.0, 0, 'amarillo'),    # 3.0 no es < 3.0
        (2.99, 0, 'rojo'),
        (3.5, 0, 'verde'),       # 3.5 no es < 3.5
        (3.49, 0, 'amarillo'),
        (5.0, 50, 'rojo'),       # pct >= 50
        (5.0, 49.99, 'amarillo'),
        (5.0, 25, 'amarillo'),   # pct >= 25
        (5.0, 24.99, 'verde'),
    ])
    def test_limites(self, _mock, nota, pct, esperado):
        assert clasificar_semaforo(nota, pct) == esperado

    def test_sin_actividades_es_verde(self, _mock):
        assert clasificar_semaforo(0, 0, tiene_actividades=False) == 'verde'
        _mock.assert_not_called()

    def test_umbrales_explicitos_no_consultan_bd(self, _mock):
        assert clasificar_semaforo(2.8, 10, umbrales=UMBRALES_DEFECTO) == 'rojo'
        _mock.assert_not_called()


class TestObtenerUmbrales:

    @patch('apps.reportes.services._get_parametro', side_effect=_sin_parametros)
    def test_valores_por_defecto(self, _mock):
        assert obtener_umbrales() == UMBRALES_DEFECTO

    @patch('apps.reportes.services._get_parametro')
    def test_umbrales_configurables(self, mock_param):
        valores = {'umbral_nota_alerta': Decimal('4.0'), 'umbral_porcentaje_alerta': 10}
        mock_param.side_effect = lambda clave, default: valores.get(clave, default)

        assert clasificar_semaforo(3.8, 0) == 'amarillo'
        assert clasificar_semaforo(4.5, 15) == 'amarillo'
        assert clasificar_semaforo(4.5, 5) == 'verde'
