"""
HU-030 — Proceso en segundo plano (run_scheduler).
"""
from unittest.mock import MagicMock, patch

from django.core.management import call_command

from apps.alertas.management.commands import run_scheduler


def _tareas(*funciones, minutos=60):
    return [(f'tarea{i}', f, minutos) for i, f in enumerate(funciones)]


def test_once_ejecuta_todas_las_tareas_y_termina():
    a, b = MagicMock(), MagicMock()
    with patch.object(run_scheduler, 'TAREAS', _tareas(a, b)):
        call_command('run_scheduler', '--once')
    a.assert_called_once()
    b.assert_called_once()


def test_error_en_una_tarea_no_detiene_las_demas():
    falla = MagicMock(side_effect=RuntimeError('boom'))
    ok = MagicMock()
    with patch.object(run_scheduler, 'TAREAS', _tareas(falla, ok)):
        call_command('run_scheduler', '--once')
    ok.assert_called_once()


def test_respeta_el_intervalo_entre_ejecuciones():
    tarea = MagicMock()
    ultima = {}
    with patch.object(run_scheduler, 'TAREAS', _tareas(tarea, minutos=60)):
        run_scheduler.correr_tareas(ultima, ahora=0)
        run_scheduler.correr_tareas(ultima, ahora=59 * 60)   # aún no se cumple
        run_scheduler.correr_tareas(ultima, ahora=60 * 60)   # ya se cumplió
    assert tarea.call_count == 2


@patch('apps.reportes.services._get_parametro', return_value=15)
def test_intervalo_de_alertas_se_lee_de_parametro_sistema(mock_param):
    assert run_scheduler._intervalo_minutos('alertas', 60) == 15
    mock_param.assert_called_once_with('intervalo_alertas_minutos', 60)


@patch('apps.reportes.services._get_parametro', side_effect=ValueError)
def test_intervalo_invalido_usa_valor_por_defecto(mock_param):
    assert run_scheduler._intervalo_minutos('alertas', 60) == 60


def test_alertas_corre_cada_15_minutos_por_defecto():
    """RNF27 / SCRUM-594: alertas en segundo plano cada 15 minutos."""
    intervalos = {nombre: minutos for nombre, _, minutos in run_scheduler.TAREAS}
    assert intervalos['alertas'] == 15
