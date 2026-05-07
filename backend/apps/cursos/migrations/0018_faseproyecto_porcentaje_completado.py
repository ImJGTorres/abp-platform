from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0017_avanceactividad'),
    ]

    operations = [
        migrations.AddField(
            model_name='faseproyecto',
            name='porcentaje_completado',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
