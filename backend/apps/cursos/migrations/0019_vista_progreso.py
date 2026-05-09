from django.db import migrations

# Vista de resumen de progreso por fase.
# Expone conteos de actividades por estado directamente desde la BD,
# sin necesidad de queries adicionales desde Python.
_SQL_VISTA_FASE = """
CREATE VIEW vista_progreso_fase AS
SELECT
    fp.id                                                               AS id_fase,
    fp.nombre                                                           AS nombre_fase,
    fp.estado                                                           AS estado_fase,
    fp.orden                                                            AS orden,
    fp.id_proyecto_id                                                   AS id_proyecto,
    fp.porcentaje_completado                                            AS porcentaje_almacenado,
    COUNT(DISTINCT a.id)                                                AS total_actividades,
    COUNT(DISTINCT CASE WHEN a.estado = 'completada'  THEN a.id END)   AS actividades_completadas,
    COUNT(DISTINCT CASE WHEN a.estado = 'en_progreso' THEN a.id END)   AS actividades_en_progreso,
    COUNT(DISTINCT CASE WHEN a.estado = 'bloqueada'   THEN a.id END)   AS actividades_bloqueadas
FROM fase_proyecto fp
LEFT JOIN actividad a ON a.id_fase_id = fp.id
GROUP BY
    fp.id,
    fp.nombre,
    fp.estado,
    fp.orden,
    fp.id_proyecto_id,
    fp.porcentaje_completado
"""

# Vista de resumen de progreso por proyecto.
# Consolida el porcentaje promedio de sus fases y los conteos de actividades
# en una sola pasada, evitando N+1 en el listado de proyectos.
_SQL_VISTA_PROYECTO = """
CREATE VIEW vista_progreso_proyecto AS
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
GROUP BY p.id, p.nombre, p.estado
"""

_SQL_BORRAR_VISTAS = """
DROP VIEW IF EXISTS vista_progreso_proyecto;
DROP VIEW IF EXISTS vista_progreso_fase;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0018_faseproyecto_porcentaje_completado'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_SQL_VISTA_FASE + ';\n' + _SQL_VISTA_PROYECTO,
            reverse_sql=_SQL_BORRAR_VISTAS,
        ),
    ]
