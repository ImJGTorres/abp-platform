from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0018_faseproyecto_porcentaje_completado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='responsables',
            field=models.ManyToManyField(
                blank=True,
                related_name='actividades_asignadas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
