import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entregables', '0004_entregable_versiones'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='entregable',
            name='retroalimentacion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='entregable',
            name='id_docente_validador',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='entregables_validados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='entregable',
            name='fecha_validacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
