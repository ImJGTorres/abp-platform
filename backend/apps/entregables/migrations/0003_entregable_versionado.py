import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entregables', '0002_archivo_adjunto'),
    ]

    operations = [
        migrations.AddField(
            model_name='entregable',
            name='numero_version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='entregable',
            name='id_version_anterior',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='versiones_siguientes',
                to='entregables.entregable',
            ),
        ),
    ]
