"""
HU-26 BD02 – Constraint único de autoevaluación por periodo.

Agrega UniqueConstraint sobre (id_proyecto, id_estudiante, periodo_evaluacion)
para garantizar que cada estudiante solo pueda tener una autoevaluación
por proyecto y por periodo de evaluación.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0009_hu26_bd01_autoevaluacion'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='autoevaluacion',
            constraint=models.UniqueConstraint(
                fields=['id_proyecto', 'id_estudiante', 'periodo_evaluacion'],
                name='unique_autoevaluacion_por_periodo',
            ),
        ),
    ]