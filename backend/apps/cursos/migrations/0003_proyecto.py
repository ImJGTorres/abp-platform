import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0002_curso_campos_adicionales'),
    ]

    operations = [
        migrations.CreateModel(
            name='Proyecto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('estado', models.CharField(
                    choices=[
                        ('planificado', 'Planificado'),
                        ('en_ejecucion', 'En Ejecución'),
                        ('finalizado', 'Finalizado'),
                    ],
                    default='planificado',
                    max_length=15,
                )),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin_estimada', models.DateField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_curso', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='proyecto',
                    to='cursos.curso',
                )),
            ],
            options={
                'db_table': 'proyecto',
            },
        ),
    ]