from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('configuracion', '0006_parametros_pesos_nota'),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO parametro_sistema
                    (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES
                    ('umbral_nota_alerta', '3.5',
                     'Nota promedio por debajo de la cual el semáforo de rendimiento pasa a amarillo (escala 0-5)',
                     'general', 'float', NOW()),
                    ('umbral_porcentaje_alerta', '25',
                     'Porcentaje de actividades incumplidas a partir del cual el semáforo de rendimiento pasa a amarillo',
                     'general', 'integer', NOW())
                ON CONFLICT (clave) DO NOTHING;
            """,
            reverse_sql="""
                DELETE FROM parametro_sistema
                WHERE clave IN (
                    'umbral_nota_alerta', 'umbral_porcentaje_alerta'
                );
            """,
        ),
    ]
