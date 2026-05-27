import os
import uuid
from django.conf import settings
from django.utils import timezone


def _ruta_exportacion(formato):
    directorio = os.path.join(settings.MEDIA_ROOT, 'exportaciones')
    os.makedirs(directorio, exist_ok=True)
    ext = 'pdf' if formato == 'pdf' else 'xlsx'
    nombre = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join(directorio, nombre)


def _obtener_datos(tipo_reporte, parametros):
    from apps.reportes.services import (
        reporte_proyecto,
        reporte_estudiante_proyecto,
        indicadores_dashboard,
        indicadores_tendencia,
        reporte_equipo_estudiantes,
    )
    if tipo_reporte == 'proyecto':
        return reporte_proyecto(parametros['proyecto_id'])
    if tipo_reporte == 'estudiante':
        return reporte_estudiante_proyecto(
            parametros['estudiante_id'], parametros['proyecto_id']
        )
    if tipo_reporte == 'indicadores':
        return indicadores_dashboard(
            periodo_id=parametros.get('periodo_id'),
            curso_id=parametros.get('curso_id'),
        )
    if tipo_reporte == 'tendencia':
        return indicadores_tendencia(n_periodos=parametros.get('n_periodos', 4))
    if tipo_reporte == 'equipo':
        return reporte_equipo_estudiantes(parametros['equipo_id'])
    raise ValueError(f"tipo_reporte desconocido: {tipo_reporte}")


def generar_exportacion(exportacion_id):
    from apps.exportaciones.models import Exportacion
    from apps.exportaciones.generadores.pdf import (
        generar_pdf_proyecto, generar_pdf_estudiante, generar_pdf_indicadores
    )
    from apps.exportaciones.generadores.excel import (
        generar_excel_proyecto, generar_excel_estudiante, generar_excel_indicadores
    )

    try:
        exp = Exportacion.objects.get(id=exportacion_id)
    except Exportacion.DoesNotExist:
        return

    try:
        datos = _obtener_datos(exp.tipo_reporte, exp.parametros)
        if datos is None:
            raise ValueError("No se encontraron datos para los parámetros indicados.")

        ruta = _ruta_exportacion(exp.formato)

        if exp.formato == 'pdf':
            generadores_pdf = {
                'proyecto': generar_pdf_proyecto,
                'estudiante': generar_pdf_estudiante,
                'indicadores': generar_pdf_indicadores,
                'tendencia': generar_pdf_indicadores,
                'equipo': generar_pdf_estudiante,
            }
            fn = generadores_pdf.get(exp.tipo_reporte)
            if fn is None:
                raise ValueError(f"Sin generador PDF para tipo {exp.tipo_reporte}")
            fn(datos, ruta)
        else:
            generadores_excel = {
                'proyecto': generar_excel_proyecto,
                'estudiante': generar_excel_estudiante,
                'indicadores': generar_excel_indicadores,
                'tendencia': generar_excel_indicadores,
                'equipo': generar_excel_estudiante,
            }
            fn = generadores_excel.get(exp.tipo_reporte)
            if fn is None:
                raise ValueError(f"Sin generador Excel para tipo {exp.tipo_reporte}")
            fn(datos, ruta)

        exp.ruta_archivo = ruta
        exp.estado = 'listo'
        exp.fecha_disponible = timezone.now()
        exp.save(update_fields=['ruta_archivo', 'estado', 'fecha_disponible'])

    except Exception as e:
        exp.estado = 'error'
        exp.mensaje_error = str(e)
        exp.save(update_fields=['estado', 'mensaje_error'])
