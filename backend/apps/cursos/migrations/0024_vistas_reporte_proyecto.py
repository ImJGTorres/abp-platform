from django.db import migrations


CREAR_VISTAS = """
-- Vista: resumen de entregables por proyecto
CREATE OR REPLACE VIEW vista_entregables_proyecto AS
SELECT
    ee.proyecto_id,
    COUNT(DISTINCT e.id)                                                      AS total_entregables,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'aprobado')                 AS aprobados,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'rechazado')                AS rechazados,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'enviado')                  AS enviados,
    COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'borrador')                 AS pendientes,
    -- Tasa de entrega a tiempo: enviados/aprobados cuya fecha_envio <= fecha_limite de la actividad
    COUNT(DISTINCT e.id) FILTER (
        WHERE e.estado IN ('enviado','aprobado')
          AND e.fecha_envio IS NOT NULL
          AND e.fecha_envio::date <= a.fecha_limite
    )                                                                          AS entregados_a_tiempo,
    ROUND(
        100.0 * COUNT(DISTINCT e.id) FILTER (
            WHERE e.estado IN ('enviado','aprobado')
              AND e.fecha_envio IS NOT NULL
              AND e.fecha_envio::date <= a.fecha_limite
        ) / NULLIF(COUNT(DISTINCT e.id) FILTER (WHERE e.estado IN ('enviado','aprobado','rechazado')), 0),
        2
    )                                                                          AS tasa_entrega_tiempo_pct
FROM entregable e
JOIN actividad a         ON a.id = e.id_actividad_id
JOIN equipos_equipo ee   ON ee.id = e.id_equipo_id
GROUP BY ee.proyecto_id;

-- Vista: avance promedio por estudiante y proyecto
CREATE OR REPLACE VIEW vista_avance_estudiante_proyecto AS
SELECT
    em.usuario_id,
    ee.proyecto_id,
    ROUND(AVG(av.porcentaje_completado)::numeric, 2)   AS promedio_avance_pct,
    ROUND((AVG(av.porcentaje_completado) / 100.0 * 5)::numeric, 2) AS nota_promedio_5,
    COUNT(DISTINCT av.id_actividad_id)                 AS actividades_con_avance
FROM avance_actividad av
JOIN actividad a              ON a.id = av.id_actividad_id
JOIN equipos_equipo ee        ON ee.id = a.id_equipo_asignado_id
JOIN equipos_miembroequipo em ON em.equipo_id = ee.id AND em.estado = 'activo'
WHERE av.id_usuario_id = em.usuario_id
GROUP BY em.usuario_id, ee.proyecto_id;
"""

ELIMINAR_VISTAS = """
DROP VIEW IF EXISTS vista_avance_estudiante_proyecto;
DROP VIEW IF EXISTS vista_entregables_proyecto;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('cursos', '0023_fix_usuario_fk_set_null'),
    ]
    operations = [
        migrations.RunSQL(sql=CREAR_VISTAS, reverse_sql=ELIMINAR_VISTAS),
    ]
