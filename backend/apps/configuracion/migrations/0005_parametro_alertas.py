from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('configuracion', '0004_parametros_bajo_rendimiento'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                INSERT INTO parametro_sistema (clave, valor, descripcion, categoria, tipo_dato, fecha_actualizacion)
                VALUES ('frecuencia_alertas_horas', '24',
                        'Cada cuántas horas se ejecuta el servicio de generación de alertas',
                        'general', 'integer', NOW())
                ON CONFLICT (clave) DO NOTHING;
            """,
            reverse_sql="DELETE FROM parametro_sistema WHERE clave = 'frecuencia_alertas_horas';",
        ),
    ]
