import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0016_alter_cursoestudiante_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AvanceActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.TextField()),
                ('porcentaje_completado', models.PositiveSmallIntegerField()),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('tipo', models.CharField(
                    choices=[('texto', 'Texto'), ('enlace', 'Enlace')],
                    default='texto',
                    max_length=6,
                )),
                ('url_referencia', models.URLField(blank=True, null=True)),
                ('id_actividad', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='avances',
                    to='cursos.actividad',
                )),
                ('id_usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='avances_registrados',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'avance_actividad',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.AddConstraint(
            model_name='avanceactividad',
            constraint=models.CheckConstraint(
                check=models.Q(porcentaje_completado__gte=0) & models.Q(porcentaje_completado__lte=100),
                name='avance_porcentaje_0_100',
            ),
        ),
    ]
