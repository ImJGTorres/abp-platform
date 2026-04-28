import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0001_initial'),
        ('cursos', '0005_resultadoaprendizaje'),
    ]

    operations = [
        migrations.AddField(
            model_name='criteriorubrica',
            name='rap',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='criterios',
                to='cursos.resultadoaprendizaje',
            ),
        ),
    ]
