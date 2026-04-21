import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0001_initial'),
        ('configuracion', '0002_update_usuario_modifico'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Agregar campo codigo con default temporal para filas existentes
        migrations.AddField(
            model_name='curso',
            name='codigo',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        # Agregar FK id_docente
        migrations.AddField(
            model_name='curso',
            name='id_docente',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos_docente',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        # Agregar campo estado
        migrations.AddField(
            model_name='curso',
            name='estado',
            field=models.CharField(
                choices=[
                    ('borrador', 'Borrador'),
                    ('activo', 'Activo'),
                    ('cerrado', 'Cerrado'),
                ],
                default='borrador',
                max_length=10,
            ),
        ),
        # Agregar fecha_creacion
        migrations.AddField(
            model_name='curso',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Agregar fecha_actualizacion
        migrations.AddField(
            model_name='curso',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        # Hacer id_periodo_academico obligatorio (eliminar null=True/blank=True)
        migrations.AlterField(
            model_name='curso',
            name='id_periodo_academico',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='configuracion.periodoacademico',
            ),
        ),
        # Agregar related_name a usuario_creo para evitar conflicto con id_docente
        migrations.AlterField(
            model_name='curso',
            name='usuario_creo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cursos_creados',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Índice único compuesto: código único por periodo académico
        migrations.AddConstraint(
            model_name='curso',
            constraint=models.UniqueConstraint(
                fields=['codigo', 'id_periodo_academico'],
                name='unique_codigo_por_periodo',
            ),
        ),
    ]