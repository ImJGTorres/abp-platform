"""
HU-24 BD01 – Diseñar tabla de evaluaciones de entregable.

Crea la tabla `evaluacion`:
  id, id_entregable (FK → entregable), id_rubrica (FK → rubrica),
  id_docente (FK → usuario), puntuacion_total, comentario_general,
  fecha_evaluacion (auto_now_add), estado (borrador/publicada).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0005_bd03_niveldesempeno'),
        ('entregables', '0007_fix_usuario_fk_set_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Evaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion_total', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('comentario_general', models.TextField(blank=True, null=True)),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(
                    choices=[('borrador', 'Borrador'), ('publicada', 'Publicada')],
                    default='borrador',
                    max_length=10,
                )),
                ('id_entregable', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='evaluaciones',
                    to='entregables.entregable',
                )),
                ('id_rubrica', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='evaluaciones',
                    to='evaluacion.rubrica',
                )),
                ('id_docente', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='evaluaciones_realizadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'evaluacion',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
    ]