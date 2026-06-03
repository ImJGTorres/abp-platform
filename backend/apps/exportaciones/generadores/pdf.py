import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

ROJO = colors.HexColor('#d32f2f')
ROJO_CLARO = colors.HexColor('#ffcdd2')
GRIS_OSCURO = colors.HexColor('#424242')
GRIS_CLARO = colors.HexColor('#f5f5f5')
BLANCO = colors.white

NOMBRE_INSTITUCION = "UFPS — Plataforma ABP"
PROGRAMA = "Ingeniería de Sistemas"


def _estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('Titulo', fontName='Helvetica-Bold', fontSize=16,
                          textColor=ROJO, alignment=TA_CENTER, spaceAfter=6))
    s.add(ParagraphStyle('Subtitulo', fontName='Helvetica-Bold', fontSize=12,
                          textColor=GRIS_OSCURO, spaceAfter=4))
    s.add(ParagraphStyle('Normal2', fontName='Helvetica', fontSize=9,
                          textColor=GRIS_OSCURO, spaceAfter=2))
    s.add(ParagraphStyle('Encabezado', fontName='Helvetica-Bold', fontSize=8,
                          textColor=BLANCO, alignment=TA_CENTER))
    s.add(ParagraphStyle('Celda', fontName='Helvetica', fontSize=8,
                          textColor=GRIS_OSCURO, alignment=TA_CENTER))
    s.add(ParagraphStyle('Pie', fontName='Helvetica', fontSize=7,
                          textColor=colors.grey, alignment=TA_RIGHT))
    return s


def _estilo_tabla_base():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ROJO),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLANCO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])


def _encabezado_pagina(story, titulo, subtitulo=None):
    s = _estilos()
    story.append(Paragraph(NOMBRE_INSTITUCION, s['Normal2']))
    story.append(Paragraph(PROGRAMA, s['Normal2']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ROJO, spaceAfter=6))
    story.append(Paragraph(titulo, s['Titulo']))
    if subtitulo:
        story.append(Paragraph(subtitulo, s['Subtitulo']))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        s['Pie']
    ))
    story.append(Spacer(1, 0.4 * cm))


def generar_pdf_proyecto(datos, ruta_destino):
    s = _estilos()
    doc = SimpleDocTemplate(ruta_destino, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []
    proy = datos.get('proyecto', {})

    _encabezado_pagina(story, 'Reporte de Proyecto',
                       subtitulo=proy.get('nombre', ''))

    info_rows = [
        ['Campo', 'Valor'],
        ['Estado', proy.get('estado', '-')],
        ['Curso', proy.get('curso', '-')],
        ['Fecha inicio', proy.get('fecha_inicio', '-')],
        ['Fecha fin estimada', proy.get('fecha_fin_estimada', '-')],
    ]
    t = Table(info_rows, colWidths=[5*cm, 11*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    prog = datos.get('progreso_global', {})
    story.append(Paragraph('Progreso Global', s['Subtitulo']))
    prog_rows = [
        ['Indicador', 'Valor'],
        ['Progreso (%)', str(prog.get('porcentaje_progreso', 0))],
        ['Total fases', str(prog.get('total_fases', 0))],
        ['Fases completadas', str(prog.get('fases_completadas', 0))],
        ['Total actividades', str(prog.get('total_actividades', 0))],
        ['Actividades completadas', str(prog.get('actividades_completadas', 0))],
    ]
    t = Table(prog_rows, colWidths=[8*cm, 8*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph('Progreso por Fase', s['Subtitulo']))
    fases = datos.get('progreso_por_fase', [])
    if fases:
        fase_rows = [['Fase', 'Estado', 'Avance (%)', 'Actividades', 'Completadas']]
        for f in fases:
            fase_rows.append([
                f.get('nombre_fase', '-'),
                f.get('estado_fase', '-'),
                str(f.get('porcentaje_almacenado', 0)),
                str(f.get('total_actividades', 0)),
                str(f.get('actividades_completadas', 0)),
            ])
        t = Table(fase_rows, colWidths=[5*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm])
        t.setStyle(_estilo_tabla_base())
        story.append(t)
    story.append(Spacer(1, 0.4*cm))

    ents = datos.get('resumen_entregables', {})
    story.append(Paragraph('Resumen de Entregables', s['Subtitulo']))
    ent_rows = [
        ['Indicador', 'Valor'],
        ['Total', str(ents.get('total_entregables', 0))],
        ['Aprobados', str(ents.get('aprobados', 0))],
        ['Rechazados', str(ents.get('rechazados', 0))],
        ['Tasa entrega a tiempo (%)', str(ents.get('tasa_entrega_tiempo_pct', 0))],
    ]
    t = Table(ent_rows, colWidths=[8*cm, 8*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    bajo = datos.get('estudiantes_bajo_rendimiento', [])
    story.append(Paragraph(
        f'Estudiantes en Bajo Rendimiento (umbral: {datos.get("umbral_bajo_rendimiento", 3.0)})',
        s['Subtitulo']
    ))
    if bajo:
        bajo_rows = [['Nombre', 'Código', 'Nota Promedio (0-5)', 'Avance (%)']]
        for e in bajo:
            bajo_rows.append([
                f"{e.get('nombre','')} {e.get('apellido','')}",
                e.get('codigo', '-'),
                str(e.get('nota_promedio_5', '-')),
                str(e.get('promedio_avance_pct', '-')),
            ])
        t = Table(bajo_rows, colWidths=[5*cm, 3*cm, 4*cm, 4*cm])
        t.setStyle(_estilo_tabla_base())
        story.append(t)
    else:
        story.append(Paragraph('Sin estudiantes en bajo rendimiento.', s['Normal2']))

    doc.build(story)
    return ruta_destino


def generar_pdf_estudiante(datos, ruta_destino):
    s = _estilos()
    doc = SimpleDocTemplate(ruta_destino, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []
    est = datos.get('estudiante', {})
    proy = datos.get('proyecto', {})

    _encabezado_pagina(story, 'Reporte Individual de Estudiante',
                       subtitulo=f"{est.get('nombre','')} {est.get('apellido','')} — {proy.get('nombre','')}")

    nota = datos.get('nota_final', {})
    story.append(Paragraph('Nota Final', s['Subtitulo']))
    nota_rows = [
        ['Componente', 'Nota (0-5)', 'Peso aplicado (%)'],
    ]
    for comp, vals in nota.get('componentes', {}).items():
        nota_rows.append([comp.replace('_', ' ').title(),
                          str(vals.get('nota', '-')),
                          str(vals.get('peso_aplicado', '-'))])
    nota_rows.append(['NOTA FINAL', str(nota.get('nota_final', '-')), ''])
    t = Table(nota_rows, colWidths=[6*cm, 5*cm, 5*cm])
    ts = _estilo_tabla_base()
    ts.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ts.add('BACKGROUND', (0, -1), (-1, -1), ROJO_CLARO)
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    desemp = datos.get('desempeno', {})
    story.append(Paragraph('Indicadores de Desempeño', s['Subtitulo']))
    d_rows = [
        ['Indicador', 'Valor'],
        ['Actividades completadas', f"{desemp.get('actividades_completadas',0)} / {desemp.get('total_actividades_equipo',0)}"],
        ['Actividades vencidas', str(desemp.get('actividades_vencidas', 0))],
        ['Avance promedio (%)', str(desemp.get('promedio_avance_pct', 0))],
        ['Entregables aprobados', f"{desemp.get('entregables_aprobados',0)} / {desemp.get('total_entregables',0)}"],
        ['Entregables rechazados', str(desemp.get('entregables_rechazados', 0))],
        ['Entregados a tiempo', str(desemp.get('entregables_a_tiempo', 0))],
    ]
    t = Table(d_rows, colWidths=[8*cm, 8*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph('Historial de Entregables', s['Subtitulo']))
    hist = datos.get('historial_entregables', [])
    if hist:
        h_rows = [['Título', 'Estado', 'Versión', 'A tiempo', 'Retroalimentación']]
        for e in hist:
            retro = (e.get('retroalimentacion') or '')[:60]
            if len(e.get('retroalimentacion') or '') > 60:
                retro += '…'
            h_rows.append([
                e.get('titulo', '-')[:30],
                e.get('estado', '-'),
                str(e.get('numero_version', '-')),
                'Sí' if e.get('entregado_a_tiempo') else ('No' if e.get('entregado_a_tiempo') is False else '-'),
                retro,
            ])
        t = Table(h_rows, colWidths=[3.5*cm, 2*cm, 1.5*cm, 1.5*cm, 7.5*cm])
        t.setStyle(_estilo_tabla_base())
        story.append(t)

    doc.build(story)
    return ruta_destino


def generar_pdf_indicadores(datos, ruta_destino):
    s = _estilos()
    doc = SimpleDocTemplate(ruta_destino, pagesize=landscape(A4),
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []

    _encabezado_pagina(story, 'Dashboard de Indicadores Institucionales')

    resumen_raw = datos.get('resumen_periodo', {})
    periodos_list = resumen_raw if isinstance(resumen_raw, list) else [resumen_raw]

    story.append(Paragraph('Resumen por Periodo', s['Subtitulo']))
    r_rows = [['Periodo', 'Cursos', 'Estudiantes', 'Proyectos activos', 'Avance prom. (%)', 'Aprobación (%)']]
    for resumen in periodos_list:
        r_rows.append([
            resumen.get('periodo_nombre', '-'),
            str(resumen.get('total_cursos', 0)),
            str(resumen.get('total_estudiantes', 0)),
            str(resumen.get('proyectos_activos', 0)),
            str(resumen.get('avance_promedio_proyectos_pct', 0)),
            str(resumen.get('tasa_aprobacion_pct', 0)),
        ])
    t = Table(r_rows, colWidths=[3.5*cm, 2*cm, 2.5*cm, 3.5*cm, 3*cm, 2.5*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    dist = datos.get('distribucion_notas', {})
    story.append(Paragraph('Distribución de Notas (escala 0-5)', s['Subtitulo']))
    dn_rows = [
        ['Rango', 'Cantidad de estudiantes'],
        ['0.0 – 1.9', str(dist.get('rango_0_2', 0))],
        ['2.0 – 2.9', str(dist.get('rango_2_3', 0))],
        ['3.0 – 3.9', str(dist.get('rango_3_4', 0))],
        ['4.0 – 5.0', str(dist.get('rango_4_5', 0))],
        ['Nota promedio global', str(dist.get('nota_promedio_global', 0))],
    ]
    t = Table(dn_rows, colWidths=[10*cm, 10*cm])
    t.setStyle(_estilo_tabla_base())
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    proyectos = datos.get('proyectos', [])
    if proyectos:
        story.append(Paragraph('Proyectos', s['Subtitulo']))
        p_rows = [['Nombre', 'Curso', 'Estado', 'Avance (%)', 'Entregables', 'Aprobados']]
        for p in proyectos:
            p_rows.append([
                str(p.get('nombre', '-'))[:25],
                str(p.get('curso_nombre', '-'))[:20],
                str(p.get('estado', '-')),
                str(p.get('porcentaje_progreso', 0)),
                str(p.get('total_entregables', 0)),
                str(p.get('entregables_aprobados', 0)),
            ])
        t = Table(p_rows, colWidths=[5*cm, 4*cm, 3*cm, 3*cm, 3*cm, 3*cm])
        t.setStyle(_estilo_tabla_base())
        story.append(t)

    doc.build(story)
    return ruta_destino
