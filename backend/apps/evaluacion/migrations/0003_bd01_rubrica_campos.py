"""
BD01 – Diseñar tabla de rúbricas.

Agrega los campos requeridos a la tabla `rubrica`:
  id_proyecto (FK → proyecto, nullable), id_docente (FK → usuario, nullable),
  nombre, descripcion, tipo, peso_total, fecha_creacion.
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0002_criteriorubrica_rap'),
        ('cursos', '0023_fix_usuario_fk_set_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='rubrica',
            name='nombre',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rubrica',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rubrica',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('entregable',   'Entregable'),
                    ('proceso',      'Proceso'),
                    ('presentacion', 'Presentación'),
                ],
                default='entregable',
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name='rubrica',
            name='peso_total',
            field=models.DecimalField(decimal_places=2, default=100, max_digits=5),
        ),
        migrations.AddField(
            model_name='rubrica',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rubrica',
            name='id_proyecto',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rubricas',
                to='cursos.proyecto',
            ),
        ),
        migrations.AddField(
            model_name='rubrica',
            name='id_docente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rubricas_creadas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='rubrica',
            options={'ordering': ['-fecha_creacion']},
        ),
    ]