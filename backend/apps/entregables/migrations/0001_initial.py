import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cursos', '0014_actividad_actividaddependencia'),
        ('equipos', '0002_miembroequipo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entregable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255)),
                ('descripcion', models.TextField()),
                ('tipo', models.CharField(
                    choices=[
                        ('documento', 'Documento'),
                        ('prototipo', 'Prototipo'),
                        ('codigo', 'Código'),
                        ('presentacion', 'Presentación'),
                        ('otro', 'Otro'),
                    ],
                    max_length=30,
                )),
                ('estado', models.CharField(
                    choices=[
                        ('borrador', 'Borrador'),
                        ('enviado', 'Enviado'),
                        ('aprobado', 'Aprobado'),
                        ('rechazado', 'Rechazado'),
                    ],
                    default='borrador',
                    max_length=20,
                )),
                ('fecha_envio', models.DateTimeField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('id_actividad', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='entregables',
                    to='cursos.actividad',
                )),
                ('id_equipo', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='entregables',
                    to='equipos.equipo',
                )),
            ],
            options={
                'db_table': 'entregable',
            },
        ),
    ]
