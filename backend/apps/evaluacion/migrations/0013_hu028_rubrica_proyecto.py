from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0012_alter_autoevaluacion_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rubrica',
            name='es_rubrica_proyecto',
            field=models.BooleanField(default=False),
        ),
    ]
