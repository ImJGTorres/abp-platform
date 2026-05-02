import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0004_alter_proyecto_id_curso'),
        ('cursos', '0004_curso_cantidad_max_estudiantes_proyecto_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResultadoAprendizaje',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('descripcion', models.TextField()),
                ('competencia_asociada', models.CharField(blank=True, max_length=200, null=True)),
                ('proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='raps',
                    to='cursos.proyecto',
                )),
            ],
            options={
                'db_table': 'resultado_aprendizaje',
                'ordering': ['id'],
            },
        ),
    ]
