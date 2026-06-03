from django.db import migrations

CREAR = """
CREATE OR REPLACE VIEW vista_desempeno_estudiante AS
SELECT
    em.usuario_id,
    ee.proyecto_id,
    ee.id                                                         AS equipo_id,
    ee.nombre                                                     AS equipo_nombre,

    -- Actividades
    COUNT(DISTINCT a.id)                                          AS total_actividades_equipo,
    COUNT(DISTINCT a.id) FILTER (WHERE a.estado = 'completada')  AS actividades_completadas,
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.estado != 'completada'
          AND a.fecha_limite < CURRENT_DATE
    )                                                             AS actividades_vencidas,

    -- Avances del estudiante
    COUNT(DISTINCT av.id)                                         AS total_avances_registrados,
    ROUND(AVG(av.porcentaje_completado)::numeric, 2)              AS promedio_avance_pct,
    ROUND((AVG(av.porcentaje_completado) / 100.0 * 5)::numeric, 2) AS nota_docente_5,

    -- Entregables del equipo
    COUNT(DISTINCT e.id)                                          AS total_entregables,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'aprobado')    AS entregables_aprobados,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'rechazado')   AS entregables_rechazados,
    COUNT(DISTINCT e.id) FILTER (
        WHERE e.estado IN ('aprobado', 'enviado')
          AND e.fecha_envio IS NOT NULL
          AND e.fecha_envio::date <= a2.fecha_limite
    )                                                             AS entregables_a_tiempo

FROM equipos_miembroequipo em
JOIN equipos_equipo ee          ON ee.id = em.equipo_id AND em.estado = 'activo'
JOIN fase_proyecto fp            ON fp.id_proyecto_id = ee.proyecto_id
JOIN actividad a                 ON a.id_fase_id = fp.id
                                 AND (a.id_equipo_asignado_id = ee.id
                                      OR a.id_responsable_id = em.usuario_id)
LEFT JOIN avance_actividad av    ON av.id_actividad_id = a.id
                                 AND av.id_usuario_id = em.usuario_id
LEFT JOIN entregable e           ON e.id_equipo_id = ee.id
LEFT JOIN actividad a2           ON a2.id = e.id_actividad_id
GROUP BY em.usuario_id, ee.proyecto_id, ee.id, ee.nombre;
"""

ELIMINAR = "DROP VIEW IF EXISTS vista_desempeno_estudiante;"


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0024_vistas_reporte_proyecto'),
    ]
    operations = [
        migrations.RunSQL(sql=CREAR, reverse_sql=ELIMINAR),
    ]
