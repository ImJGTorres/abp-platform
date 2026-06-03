from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('configuracion', '0003_fix_usuario_fk_set_null'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO parametro_sistema (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES
                  ('umbral_nota_bajo_rendimiento', '3.0',
                   'Nota promedio por debajo de la cual se considera bajo rendimiento (escala 0-5)',
                   'rendimiento', 'float',
                   NOW())
                ON CONFLICT (clave) DO NOTHING;

                INSERT INTO parametro_sistema (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES
                  ('umbral_porcentaje_actividades_incumplidas', '50',
                   'Porcentaje mínimo de actividades incumplidas (completadas < 100%) para alerta',
                   'rendimiento', 'integer',
                   NOW())
                ON CONFLICT (clave) DO NOTHING;

                INSERT INTO parametro_sistema (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES
                  ('umbral_entregables_rechazados', '2',
                   'Número mínimo de entregables rechazados para alerta de bajo rendimiento',
                   'rendimiento', 'integer',
                   NOW())
                ON CONFLICT (clave) DO NOTHING;
            """,
            reverse_sql="""
                DELETE FROM parametro_sistema
                WHERE clave IN (
                  'umbral_nota_bajo_rendimiento',
                  'umbral_porcentaje_actividades_incumplidas',
                  'umbral_entregables_rechazados'
                );
            """,
        ),
    ]
