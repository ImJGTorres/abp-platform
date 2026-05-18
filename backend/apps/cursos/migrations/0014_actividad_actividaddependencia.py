import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0013_faseproyecto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('fecha_limite', models.DateField()),
                ('prioridad', models.CharField(
                    choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')],
                    default='media',
                    max_length=5,
                )),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('en_progreso', 'En Progreso'),
                        ('completada', 'Completada'),
                        ('bloqueada', 'Bloqueada'),
                    ],
                    default='pendiente',
                    max_length=12,
                )),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_fase', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='actividades',
                    to='cursos.faseproyecto',
                )),
            ],
            options={
                'db_table': 'actividad',
                'ordering': ['fecha_limite', 'prioridad'],
            },
        ),
        migrations.CreateModel(
            name='ActividadDependencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_actividad', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dependencias',
                    to='cursos.actividad',
                )),
                ('id_actividad_predecesor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sucesores',
                    to='cursos.actividad',
                )),
            ],
            options={
                'db_table': 'actividad_depende_de',
            },
        ),
        migrations.AddConstraint(
            model_name='actividaddependencia',
            constraint=models.UniqueConstraint(
                fields=['id_actividad', 'id_actividad_predecesor'],
                name='unique_dependencia_actividad',
            ),
        ),
        migrations.AddConstraint(
            model_name='actividaddependencia',
            constraint=models.CheckConstraint(
                check=~models.Q(id_actividad=models.F('id_actividad_predecesor')),
                name='no_autoref_dependencia',
            ),
        ),
    ]
