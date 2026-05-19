"""
HU-24 BD02 – Diseñar tabla de calificaciones por criterio.

Crea la tabla `calificacion_criterio`:
  id, id_evaluacion (FK → evaluacion), id_criterio (FK → criterio_rubrica),
  id_nivel_seleccionado (FK → nivel_desempeno), puntos_obtenidos, comentario_criterio.

Restricción unique_criterio_por_evaluacion garantiza que cada criterio
se califica exactamente una vez por evaluación.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0006_hu24_bd01_evaluacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalificacionCriterio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntos_obtenidos', models.DecimalField(decimal_places=2, max_digits=5)),
                ('comentario_criterio', models.TextField(blank=True, null=True)),
                ('id_evaluacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='calificaciones',
                    to='evaluacion.evaluacion',
                )),
                ('id_criterio', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='calificaciones',
                    to='evaluacion.criteriorubrica',
                )),
                ('id_nivel_seleccionado', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='calificaciones',
                    to='evaluacion.niveldesempeno',
                )),
            ],
            options={
                'db_table': 'calificacion_criterio',
            },
        ),
        migrations.AddConstraint(
            model_name='calificacioncriterio',
            constraint=models.UniqueConstraint(
                fields=['id_evaluacion', 'id_criterio'],
                name='unique_criterio_por_evaluacion',
            ),
        ),
    ]