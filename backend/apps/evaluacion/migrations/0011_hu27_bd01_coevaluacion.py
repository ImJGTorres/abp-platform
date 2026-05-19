"""
HU-27 BD01 – Diseñar tabla de coevaluaciones.

Crea la tabla `coevaluacion`:
  id, id_proyecto (FK → proyecto), id_evaluador (FK → usuario),
  id_evaluado (FK → usuario), id_rubrica (FK → rubrica),
  puntuacion_total, comentario, fecha_registro,
  estado (borrador/enviada), periodo_evaluacion.
  CheckConstraint: evaluador ≠ evaluado.
  UniqueConstraint: (id_evaluador, id_evaluado, periodo_evaluacion).

Crea también la tabla `detalle_coevaluacion`:
  id, id_coevaluacion (FK), id_criterio (FK), id_nivel_seleccionado (FK),
  puntos_obtenidos, comentario.
  UniqueConstraint: (id_coevaluacion, id_criterio).
"""
import django.db.models.deletion
import django.db.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0010_hu26_bd02_constraint_autoevaluacion'),
        ('cursos', '0023_fix_usuario_fk_set_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coevaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion_total', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(
                    choices=[('borrador', 'Borrador'), ('enviada', 'Enviada')],
                    default='borrador',
                    max_length=10,
                )),
                ('periodo_evaluacion', models.CharField(max_length=50)),
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coevaluaciones',
                    to='cursos.proyecto',
                )),
                ('id_evaluador', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coevaluaciones_realizadas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('id_evaluado', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coevaluaciones_recibidas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('id_rubrica', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='coevaluaciones',
                    to='evaluacion.rubrica',
                )),
            ],
            options={
                'db_table': 'coevaluacion',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.AddConstraint(
            model_name='coevaluacion',
            constraint=models.UniqueConstraint(
                fields=['id_evaluador', 'id_evaluado', 'periodo_evaluacion'],
                name='unique_coevaluacion_por_periodo',
            ),
        ),
        migrations.AddConstraint(
            model_name='coevaluacion',
            constraint=models.CheckConstraint(
                check=~django.db.models.Q(id_evaluador=django.db.models.F('id_evaluado')),
                name='evaluador_distinto_de_evaluado',
            ),
        ),
        migrations.CreateModel(
            name='DetalleCoevaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntos_obtenidos', models.DecimalField(decimal_places=2, max_digits=5)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('id_coevaluacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='detalles',
                    to='evaluacion.coevaluacion',
                )),
                ('id_criterio', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='coevaluaciones',
                    to='evaluacion.criteriorubrica',
                )),
                ('id_nivel_seleccionado', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='coevaluaciones',
                    to='evaluacion.niveldesempeno',
                )),
            ],
            options={
                'db_table': 'detalle_coevaluacion',
            },
        ),
        migrations.AddConstraint(
            model_name='detallecoevaluacion',
            constraint=models.UniqueConstraint(
                fields=['id_coevaluacion', 'id_criterio'],
                name='unique_criterio_por_coevaluacion',
            ),
        ),
    ]