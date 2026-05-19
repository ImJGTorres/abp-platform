"""
HU-26 BD01 – Diseñar tabla de autoevaluaciones.

Crea la tabla `autoevaluacion`:
  id, id_proyecto (FK → proyecto), id_estudiante (FK → usuario),
  id_rubrica (FK → rubrica), puntuacion_total, reflexion_texto,
  fecha_registro (auto_now_add), estado (borrador/enviada), periodo_evaluacion.

Crea también la tabla `detalle_autoevaluacion`:
  id, id_autoevaluacion (FK), id_criterio (FK), id_nivel_seleccionado (FK),
  puntos_obtenidos, comentario.
  Necesaria para el cálculo automático de puntuacion_total (BE-01).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0008_hu25_bd01_retroalimentacion'),
        ('cursos', '0023_fix_usuario_fk_set_null'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Autoevaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntuacion_total', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('reflexion_texto', models.TextField(blank=True, null=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(
                    choices=[('borrador', 'Borrador'), ('enviada', 'Enviada')],
                    default='borrador',
                    max_length=10,
                )),
                ('periodo_evaluacion', models.CharField(max_length=50)),
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='autoevaluaciones',
                    to='cursos.proyecto',
                )),
                ('id_estudiante', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='autoevaluaciones',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('id_rubrica', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='autoevaluaciones',
                    to='evaluacion.rubrica',
                )),
            ],
            options={
                'db_table': 'autoevaluacion',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.CreateModel(
            name='DetalleAutoevaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntos_obtenidos', models.DecimalField(decimal_places=2, max_digits=5)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('id_autoevaluacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='detalles',
                    to='evaluacion.autoevaluacion',
                )),
                ('id_criterio', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='autoevaluaciones',
                    to='evaluacion.criteriorubrica',
                )),
                ('id_nivel_seleccionado', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='autoevaluaciones',
                    to='evaluacion.niveldesempeno',
                )),
            ],
            options={
                'db_table': 'detalle_autoevaluacion',
            },
        ),
        migrations.AddConstraint(
            model_name='detalleautoevaluacion',
            constraint=models.UniqueConstraint(
                fields=['id_autoevaluacion', 'id_criterio'],
                name='unique_criterio_por_autoevaluacion',
            ),
        ),
    ]