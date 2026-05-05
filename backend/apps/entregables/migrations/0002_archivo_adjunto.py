import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entregables', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchivoAdjunto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_original', models.CharField(max_length=255)),
                ('nombre_almacenado', models.CharField(max_length=255)),
                ('ruta', models.CharField(max_length=500)),
                ('tipo_mime', models.CharField(max_length=100)),
                ('tamaño_bytes', models.BigIntegerField()),
                ('version', models.PositiveIntegerField(default=1)),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                ('id_entregable', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='archivos',
                    to='entregables.entregable',
                )),
                ('id_usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='archivos_subidos',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'archivo_adjunto',
                'ordering': ['-fecha_subida'],
            },
        ),
    ]
