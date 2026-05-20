from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('configuracion', '0005_parametro_alertas'),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO parametro_sistema
                    (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES
                    ('peso_evaluacion_docente', '70',
                     'Porcentaje que pondera la evaluación docente (avance reportado) en la nota final',
                     'general', 'integer', NOW()),
                    ('peso_autoevaluacion', '15',
                     'Porcentaje que pondera la autoevaluación en la nota final (reservado para uso futuro)',
                     'general', 'integer', NOW()),
                    ('peso_coevaluacion', '15',
                     'Porcentaje que pondera la coevaluación en la nota final (reservado para uso futuro)',
                     'general', 'integer', NOW())
                ON CONFLICT (clave) DO NOTHING;
            """,
            reverse_sql="""
                DELETE FROM parametro_sistema
                WHERE clave IN (
                    'peso_evaluacion_docente', 'peso_autoevaluacion', 'peso_coevaluacion'
                );
            """,
        ),
    ]
