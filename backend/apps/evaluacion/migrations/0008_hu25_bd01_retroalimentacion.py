"""
HU-25 BD01 – Diseñar tabla de retroalimentaciones.

Crea la tabla `retroalimentacion`:
  id, id_proyecto (FK → proyecto), id_docente (FK → usuario),
  id_equipo (FK → equipo, nullable), id_estudiante (FK → usuario, nullable),
  id_actividad (FK → actividad, nullable),
  tipo (grupal/individual/actividad), contenido, fecha_registro.

CheckConstraint retro_tipo_fk_consistente garantiza que cada tipo tenga
su FK obligatoria no nula.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0007_hu24_bd02_calificacioncriterio'),
        ('cursos', '0023_fix_usuario_fk_set_null'),
        ('equipos', '0002_miembroequipo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Retroalimentacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[
                        ('grupal',     'Grupal'),
                        ('individual', 'Individual'),
                        ('actividad',  'Actividad'),
                    ],
                    max_length=10,
                )),
                ('contenido', models.TextField()),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='retroalimentaciones',
                    to='cursos.proyecto',
                )),
                ('id_docente', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='retroalimentaciones_dadas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('id_equipo', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='retroalimentaciones',
                    to='equipos.equipo',
                )),
                ('id_estudiante', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='retroalimentaciones_recibidas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('id_actividad', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='retroalimentaciones',
                    to='cursos.actividad',
                )),
            ],
            options={
                'db_table': 'retroalimentacion',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.AddConstraint(
            model_name='retroalimentacion',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(tipo='grupal',     id_equipo__isnull=False) |
                    models.Q(tipo='individual', id_estudiante__isnull=False) |
                    models.Q(tipo='actividad',  id_actividad__isnull=False)
                ),
                name='retro_tipo_fk_consistente',
            ),
        ),
    ]