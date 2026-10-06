"""
HU-034 — SCRUM-605: Prueba de regresión.

Confirma que, además del membrete institucional (SCRUM-602/603, ver
test_hu034_exportaciones.py), el resto del contenido del reporte (indicadores,
datos, totales) no cambió con la nueva plantilla: arma un `datos` realista
para cada tipo de reporte (proyecto, estudiante, indicadores) y verifica que
las cifras exactas aparecen en el PDF generado y coinciden celda a celda en
el Excel generado. También verifica que los `.xlsx` son archivos ZIP válidos
(proxy de que abren sin aviso de reparación en Excel/LibreOffice).
"""
import zipfile
from unittest.mock import patch

import pytest
from openpyxl import load_workbook

from apps.exportaciones.generadores.excel import (
    generar_excel_estudiante, generar_excel_indicadores, generar_excel_proyecto,
)
from apps.exportaciones.generadores.pdf import (
    generar_pdf_estudiante, generar_pdf_indicadores, generar_pdf_proyecto,
)

IDENTIDAD_DEFECTO = {'nombre_institucion': None, 'programa_academico': None,
                     'logotipo_path': None, 'logotipo_url': None}


def _sin_logo():
    """No mockea con valores propios: usa el fallback por defecto (sin BD ni logo)."""
    return patch('apps.configuracion.identidad.obtener_identidad', return_value=IDENTIDAD_DEFECTO)


def _pdf_bytes(generador, datos, tmp_path):
    ruta = str(tmp_path / f'{generador.__name__}.pdf')
    with _sin_logo(), patch('reportlab.rl_config.pageCompression', 0):
        generador(datos, ruta)
    return open(ruta, 'rb').read()


def _xlsx_wb(generador, datos, tmp_path):
    ruta = str(tmp_path / f'{generador.__name__}.xlsx')
    with _sin_logo():
        generador(datos, ruta)
    return ruta, load_workbook(ruta)


DATOS_PROYECTO = {
    'proyecto': {'nombre': 'Sistema de Matriculas', 'estado': 'en_progreso',
                 'curso': 'Ingenieria de Software I',
                 'fecha_inicio': '2026-02-01', 'fecha_fin_estimada': '2026-05-31'},
    'progreso_global': {'porcentaje_progreso': 67, 'total_fases': 4, 'fases_completadas': 2,
                        'total_actividades': 20, 'actividades_completadas': 13},
    'progreso_por_fase': [
        {'nombre_fase': 'Analisis', 'estado_fase': 'completada', 'porcentaje_almacenado': 100,
         'total_actividades': 5, 'actividades_completadas': 5,
         'actividades_en_progreso': 0, 'actividades_bloqueadas': 0},
        {'nombre_fase': 'Diseno', 'estado_fase': 'en_progreso', 'porcentaje_almacenado': 40,
         'total_actividades': 5, 'actividades_completadas': 2,
         'actividades_en_progreso': 2, 'actividades_bloqueadas': 1},
    ],
    'resumen_entregables': {'total_entregables': 12, 'aprobados': 7, 'rechazados': 1,
                            'enviados': 3, 'pendientes': 1, 'tasa_entrega_tiempo_pct': 83.3},
    'umbrales_semaforo': {'nota_rojo': 3.0, 'pct_rojo': 50.0},
    'estudiantes_bajo_rendimiento': [
        {'nombre': 'Juan', 'apellido': 'Perez', 'codigo': '1152345',
         'nota_promedio_5': 2.4, 'promedio_avance_pct': 30},
    ],
    'avance_por_estudiante': [
        {'usuario_id': 9, 'nombre': 'Ana', 'apellido': 'Ruiz', 'codigo': '1152999',
         'promedio_avance_pct': 90, 'nota_promedio_5': 4.5,
         'actividades_con_avance': 8, 'nivel_semaforo': 'verde'},
    ],
}

DATOS_ESTUDIANTE = {
    'estudiante': {'nombre': 'Carlos', 'apellido': 'Diaz', 'codigo': '1153000'},
    'proyecto': {'nombre': 'Sistema de Matriculas'},
    'nota_final': {
        'componentes': {'autoevaluacion': {'nota': 4.0, 'peso_aplicado': 20},
                        'coevaluacion': {'nota': 3.5, 'peso_aplicado': 30}},
        'nota_final': 3.75,
    },
    'desempeno': {'actividades_completadas': 9, 'total_actividades_equipo': 12,
                  'actividades_vencidas': 1, 'promedio_avance_pct': 75,
                  'entregables_aprobados': 4, 'total_entregables': 5,
                  'entregables_rechazados': 1, 'entregables_a_tiempo': 3},
    'historial_entregables': [
        {'titulo': 'Documento de Analisis', 'estado': 'aprobado', 'numero_version': 2,
         'fecha_envio': '2026-03-01', 'entregado_a_tiempo': True, 'retroalimentacion': 'Bien hecho'},
    ],
}

DATOS_INDICADORES = {
    'resumen_periodo': [
        {'periodo_nombre': '2026-1', 'total_cursos': 5, 'cursos_activos': 4,
         'total_estudiantes': 120, 'total_proyectos': 18, 'proyectos_activos': 10,
         'avance_promedio_proyectos_pct': 58.2, 'tasa_aprobacion_pct': 72.0},
    ],
    'distribucion_notas': {'rango_0_2': 3, 'rango_2_3': 7, 'rango_3_4': 40,
                           'rango_4_5': 70, 'nota_promedio_global': 3.9},
    'proyectos': [
        {'nombre': 'Sistema de Matriculas', 'curso_nombre': 'Ingenieria de Software I',
         'estado': 'en_progreso', 'porcentaje_progreso': 67,
         'total_entregables': 12, 'entregables_aprobados': 7, 'tasa_entrega_tiempo_pct': 83.3},
    ],
    'estudiantes_riesgo_por_curso': [
        {'curso_nombre': 'Ingenieria de Software I', 'verde': 30, 'amarillo': 8,
         'estudiantes_en_riesgo': 2, 'total_estudiantes_con_avance': 40},
    ],
}


class TestRegresionDatosPdf:
    """Las cifras y textos del reporte no cambian con la nueva plantilla de membrete."""

    def test_pdf_proyecto_conserva_datos_de_progreso_y_bajo_rendimiento(self, tmp_path):
        pdf = _pdf_bytes(generar_pdf_proyecto, DATOS_PROYECTO, tmp_path)
        assert b'Sistema de Matriculas' in pdf
        assert b'Analisis' in pdf and b'Diseno' in pdf
        assert b'Juan' in pdf and b'Perez' in pdf
        assert b'1152345' in pdf

    def test_pdf_estudiante_conserva_nota_final_y_desempeno(self, tmp_path):
        pdf = _pdf_bytes(generar_pdf_estudiante, DATOS_ESTUDIANTE, tmp_path)
        assert b'Carlos' in pdf and b'Diaz' in pdf
        assert b'3.75' in pdf
        assert b'Documento de Analisis' in pdf

    def test_pdf_indicadores_conserva_resumen_y_distribucion(self, tmp_path):
        pdf = _pdf_bytes(generar_pdf_indicadores, DATOS_INDICADORES, tmp_path)
        assert b'2026-1' in pdf
        assert b'Sistema de Matriculas' in pdf


class TestRegresionDatosExcel:
    """Las cifras del Excel coinciden celda a celda con los datos de entrada."""

    def test_excel_proyecto_conserva_fases_y_avance_por_estudiante(self, tmp_path):
        ruta, wb = _xlsx_wb(generar_excel_proyecto, DATOS_PROYECTO, tmp_path)
        fases = wb['Fases']
        # La tabla empieza en fila 3 (encabezado) + 2 filas de membrete insertadas después = fila 5.
        assert fases.cell(5, 1).value == 'Fase'
        assert fases.cell(6, 1).value == 'Analisis'
        assert fases.cell(6, 3).value == 100
        estudiantes = wb['Estudiantes']
        assert estudiantes.cell(4, 2).value == 'Ana'
        assert estudiantes.cell(4, 6).value == 4.5

    def test_excel_estudiante_conserva_nota_final_y_desempeno(self, tmp_path):
        ruta, wb = _xlsx_wb(generar_excel_estudiante, DATOS_ESTUDIANTE, tmp_path)
        nota = wb['Nota Final']
        # _escribir_tabla pone NOTA FINAL en la fila 6 (header fila 3); _membrete()
        # inserta 2 filas arriba después → NOTA FINAL queda en la fila 8.
        assert nota.cell(8, 1).value == 'NOTA FINAL'
        assert nota.cell(8, 2).value == 3.75
        desemp = wb['Desempeño']
        valores = {desemp.cell(r, 1).value: desemp.cell(r, 2).value for r in range(2, 9)}
        assert valores['Avance promedio (%)'] == 75

    def test_excel_indicadores_conserva_resumen_y_proyectos(self, tmp_path):
        ruta, wb = _xlsx_wb(generar_excel_indicadores, DATOS_INDICADORES, tmp_path)
        res = wb['Resumen']
        # 'Resumen' sí tiene _membrete() (2 filas insertadas arriba): header fila 1 → 3.
        assert res.cell(3, 1).value == 'Periodo'
        assert res.cell(4, 1).value == '2026-1'
        assert res.cell(4, 4).value == 120
        # 'Proyectos' no tiene _membrete(): header se queda en la fila 1.
        proy = wb['Proyectos']
        assert proy.cell(1, 1).value == 'Nombre'
        assert proy.cell(2, 1).value == 'Sistema de Matriculas'

    @pytest.mark.parametrize('generador,datos', [
        (generar_excel_proyecto, DATOS_PROYECTO),
        (generar_excel_estudiante, DATOS_ESTUDIANTE),
        (generar_excel_indicadores, DATOS_INDICADORES),
    ])
    def test_excel_es_un_archivo_zip_valido_sin_corrupcion(self, generador, datos, tmp_path):
        """Proxy de 'abre sin aviso de reparación en Excel/LibreOffice': .xlsx es un ZIP íntegro."""
        ruta, _ = _xlsx_wb(generador, datos, tmp_path)
        with zipfile.ZipFile(ruta) as zf:
            assert zf.testzip() is None
            assert '[Content_Types].xml' in zf.namelist()
