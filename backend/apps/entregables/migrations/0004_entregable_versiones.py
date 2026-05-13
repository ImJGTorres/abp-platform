import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entregables', '0003_entregable_versionado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EntregableVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_version', models.PositiveIntegerField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('motivo_revision', models.TextField(blank=True)),
                ('id_entregable_original', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='hilo_versiones',
                    to='entregables.entregable',
                )),
                ('id_version', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='registro_version',
                    to='entregables.entregable',
                )),
                ('id_usuario', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='versiones_creadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'entregable_versiones',
                'ordering': ['numero_version'],
            },
        ),
    ]
