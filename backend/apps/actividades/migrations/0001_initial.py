import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cursos', '0012_populate_curso_estudiante'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaseProyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fases',
                    to='cursos.proyecto',
                )),
            ],
            options={
                'db_table': 'fase_proyecto',
            },
        ),
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('fecha_limite', models.DateField(blank=True, null=True)),
                ('prioridad', models.CharField(
                    choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')],
                    default='media',
                    max_length=10,
                )),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('en_progreso', 'En Progreso'),
                        ('completada', 'Completada'),
                        ('cancelada', 'Cancelada'),
                    ],
                    default='pendiente',
                    max_length=15,
                )),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_fase', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='actividades',
                    to='actividades.faseproyecto',
                )),
            ],
            options={
                'db_table': 'actividad',
            },
        ),
    ]
