import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0003_proyecto'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='cantidad_max_estudiantes',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='proyecto',
            name='id_curso',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='proyectos',
                to='cursos.curso',
            ),
        ),
    ]