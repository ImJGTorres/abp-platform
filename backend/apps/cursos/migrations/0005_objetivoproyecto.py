"""
Migración BD-01: crea la tabla objetivo_proyecto.

Campos:
  id              — PK auto.
  id_proyecto     — FK a proyecto (CASCADE: si se borra el proyecto se borran sus objetivos).
  descripcion     — Texto libre del objetivo.
  tipo            — 'general' | 'especifico'.
  orden           — Posición dentro del proyecto (único por proyecto).
  fecha_creacion  — Timestamp inmutable de creación.

Constraint: unique_orden_por_proyecto garantiza que cada número de orden
aparezca una sola vez por proyecto, sin huecos accidentales.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    # Depende de la migración que consolidó el FK de proyecto y el campo
    # cantidad_max_estudiantes en Curso.
    dependencies = [
        ('cursos', '0004_curso_cantidad_max_estudiantes_proyecto_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjetivoProyecto',
            fields=[
                # PK estándar auto-generada por Django.
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                # FK al proyecto; CASCADE asegura limpieza automática al borrar.
                ('id_proyecto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='objetivos',
                    to='cursos.proyecto',
                )),
                # Descripción textual del objetivo; sin límite de caracteres (TextField).
                ('descripcion', models.TextField()),
                # Clasificación del objetivo.
                ('tipo', models.CharField(
                    choices=[
                        ('general', 'General'),
                        ('especifico', 'Específico'),
                    ],
                    max_length=10,
                )),
                # Orden de presentación dentro del proyecto.
                ('orden', models.PositiveIntegerField()),
                # Fecha de creación inmutable; se establece automáticamente.
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'objetivo_proyecto',
                # Orden por defecto: tipo ascendente, luego orden ascendente.
                'ordering': ['tipo', 'orden'],
            },
        ),
        # Garantiza que el número de orden sea único dentro de cada proyecto.
        migrations.AddConstraint(
            model_name='objetivoproyecto',
            constraint=models.UniqueConstraint(
                fields=['id_proyecto', 'orden'],
                name='unique_orden_por_proyecto',
            ),
        ),
    ]