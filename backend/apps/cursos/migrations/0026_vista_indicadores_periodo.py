from django.db import migrations

CREAR = """
-- Indicadores agregados por periodo académico
CREATE OR REPLACE VIEW vista_indicadores_periodo AS
SELECT
    pa.id                                                               AS periodo_id,
    pa.nombre                                                           AS periodo_nombre,
    pa.fecha_inicio                                                     AS periodo_inicio,
    pa.fecha_fin                                                        AS periodo_fin,
    pa.estado                                                           AS periodo_estado,

    -- Cursos
    COUNT(DISTINCT c.id)                                                AS total_cursos,
    COUNT(DISTINCT c.id) FILTER (WHERE c.estado = 'activo')            AS cursos_activos,
    COUNT(DISTINCT c.id) FILTER (WHERE c.estado = 'cerrado')           AS cursos_cerrados,

    -- Docentes activos en el periodo
    COUNT(DISTINCT c.id_docente_id) FILTER (WHERE c.id_docente_id IS NOT NULL) AS docentes_activos,

    -- Estudiantes inscritos
    COUNT(DISTINCT ce.estudiante_id)                                    AS total_estudiantes,

    -- Proyectos
    COUNT(DISTINCT p.id)                                                AS total_proyectos,
    COUNT(DISTINCT p.id) FILTER (WHERE p.estado = 'completado')        AS proyectos_completados,
    COUNT(DISTINCT p.id) FILTER (WHERE p.estado = 'abandonado')        AS proyectos_abandonados,
    COUNT(DISTINCT p.id) FILTER (
        WHERE p.estado IN ('planificado', 'en_progreso')
    )                                                                   AS proyectos_activos,

    -- Avance promedio de proyectos (desde vista_progreso_proyecto)
    ROUND(AVG(vpp.porcentaje_progreso)::numeric, 2)                    AS avance_promedio_proyectos_pct,

    -- Entregables globales
    COALESCE(SUM(vep.total_entregables), 0)                            AS total_entregables,
    COALESCE(SUM(vep.aprobados), 0)                                    AS entregables_aprobados,
    COALESCE(SUM(vep.rechazados), 0)                                   AS entregables_rechazados,

    -- Tasa de aprobación global (aprobados / (aprobados + rechazados))
    ROUND(
        100.0 * COALESCE(SUM(vep.aprobados), 0)
        / NULLIF(COALESCE(SUM(vep.aprobados), 0) + COALESCE(SUM(vep.rechazados), 0), 0),
        2
    )                                                                   AS tasa_aprobacion_pct

FROM periodo_academico pa
LEFT JOIN curso c               ON c.id_periodo_academico_id = pa.id
LEFT JOIN curso_estudiante ce   ON ce.curso_id = c.id AND ce.estado = 'activo'
LEFT JOIN proyecto p            ON p.id_curso_id = c.id
LEFT JOIN vista_progreso_proyecto vpp ON vpp.id_proyecto = p.id
LEFT JOIN vista_entregables_proyecto vep ON vep.proyecto_id = p.id
GROUP BY pa.id, pa.nombre, pa.fecha_inicio, pa.fecha_fin, pa.estado;
"""

ELIMINAR = "DROP VIEW IF EXISTS vista_indicadores_periodo;"


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0025_vista_desempeno_individual'),
    ]
    operations = [
        migrations.RunSQL(sql=CREAR, reverse_sql=ELIMINAR),
    ]
