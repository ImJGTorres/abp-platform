import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0012_populate_curso_estudiante'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaseProyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('orden', models.PositiveIntegerField()),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('en_progreso', 'En Progreso'),
                        ('completada', 'Completada'),
                    ],
                    default='pendiente',
                    max_length=12,
                )),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fases',
                    to='cursos.proyecto',
                )),
            ],
            options={
                'db_table': 'fase_proyecto',
                'ordering': ['orden'],
            },
        ),
        migrations.AddConstraint(
            model_name='faseproyecto',
            constraint=models.UniqueConstraint(
                fields=['id_proyecto', 'orden'],
                name='unique_orden_por_fase_proyecto',
            ),
        ),
    ]
