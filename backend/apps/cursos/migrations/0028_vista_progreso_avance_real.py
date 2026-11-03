from django.db import migrations

# HU-042 (corrección): porcentaje_progreso del proyecto = promedio del avance de sus
# actividades (100 si está completada; si no, su último avance; 0 sin avance).
# Antes promediaba fase_proyecto.porcentaje_completado después del JOIN con actividad,
# así que cada fase pesaba según su número de actividades y las fases vacías contaban 0.
# Mismas columnas, tipos y orden: vista_indicadores_periodo (0026) depende de esta vista.
_SQL_NUEVA = """
CREATE OR REPLACE VIEW vista_progreso_proyecto AS
SELECT
    p.id                                                                AS id_proyecto,
    p.nombre                                                            AS nombre_proyecto,
    p.estado                                                            AS estado_proyecto,
    COUNT(DISTINCT fp.id)                                               AS total_fases,
    COUNT(DISTINCT CASE WHEN fp.estado = 'completada'  THEN fp.id END) AS fases_completadas,
    COUNT(DISTINCT CASE WHEN fp.estado = 'en_progreso' THEN fp.id END) AS fases_en_progreso,
    COALESCE(ROUND(AVG(
        CASE
            WHEN a.id IS NULL THEN NULL
            WHEN a.estado = 'completada' THEN 100
            ELSE COALESCE((
                SELECT av.porcentaje_completado
                FROM avance_actividad av
                WHERE av.id_actividad_id = a.id
                ORDER BY av.fecha_registro DESC, av.id DESC
                LIMIT 1
            ), 0)
        END
    )::numeric), 0)                                                     AS porcentaje_progreso,
    COUNT(DISTINCT a.id)                                                AS total_actividades,
    COUNT(DISTINCT CASE WHEN a.estado = 'completada'   THEN a.id END)  AS actividades_completadas
FROM proyecto p
LEFT JOIN fase_proyecto fp ON fp.id_proyecto_id = p.id
LEFT JOIN actividad a      ON a.id_fase_id = fp.id
GROUP BY p.id, p.nombre, p.estado;
"""

_SQL_ANTERIOR = """
CREATE OR REPLACE VIEW vista_progreso_proyecto AS
SELECT
    p.id                                                                AS id_proyecto,
    p.nombre                                                            AS nombre_proyecto,
    p.estado                                                            AS estado_proyecto,
    COUNT(DISTINCT fp.id)                                               AS total_fases,
    COUNT(DISTINCT CASE WHEN fp.estado = 'completada'  THEN fp.id END) AS fases_completadas,
    COUNT(DISTINCT CASE WHEN fp.estado = 'en_progreso' THEN fp.id END) AS fases_en_progreso,
    COALESCE(ROUND(AVG(fp.porcentaje_completado)::numeric), 0)         AS porcentaje_progreso,
    COUNT(DISTINCT a.id)                                                AS total_actividades,
    COUNT(DISTINCT CASE WHEN a.estado = 'completada'   THEN a.id END)  AS actividades_completadas
FROM proyecto p
LEFT JOIN fase_proyecto fp ON fp.id_proyecto_id = p.id
LEFT JOIN actividad a      ON a.id_fase_id = fp.id
GROUP BY p.id, p.nombre, p.estado;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0027_hu045_indices_busqueda'),
    ]

    operations = [
        migrations.RunSQL(sql=_SQL_NUEVA, reverse_sql=_SQL_ANTERIOR),
    ]
