"""
BD03 – Diseñar tabla de niveles de desempeño por criterio.

Crea la tabla `nivel_desempeno`:
  id, id_criterio (FK → criterio_rubrica), nivel (1-4),
  etiqueta (Insuficiente/Básico/Satisfactorio/Excelente), descripcion, puntos.

Restricciones:
  - unique_nivel_por_criterio: un criterio no puede tener dos niveles iguales.
  - nivel_entre_1_y_4: el campo `nivel` solo acepta valores del 1 al 4.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0004_bd02_criteriorubrica_peso_porcentual'),
    ]

    operations = [
        migrations.CreateModel(
            name='NivelDesempeno',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nivel', models.PositiveSmallIntegerField()),
                ('etiqueta', models.CharField(
                    choices=[
                        ('insuficiente',  'Insuficiente'),
                        ('basico',        'Básico'),
                        ('satisfactorio', 'Satisfactorio'),
                        ('excelente',     'Excelente'),
                    ],
                    max_length=13,
                )),
                ('descripcion', models.TextField()),
                ('puntos', models.DecimalField(decimal_places=2, max_digits=5)),
                ('id_criterio', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='niveles',
                    to='evaluacion.criteriorubrica',
                )),
            ],
            options={
                'db_table': 'nivel_desempeno',
                'ordering': ['nivel'],
            },
        ),
        migrations.AddConstraint(
            model_name='niveldesempeno',
            constraint=models.UniqueConstraint(
                fields=['id_criterio', 'nivel'],
                name='unique_nivel_por_criterio',
            ),
        ),
        migrations.AddConstraint(
            model_name='niveldesempeno',
            constraint=models.CheckConstraint(
                check=models.Q(nivel__gte=1) & models.Q(nivel__lte=4),
                name='nivel_entre_1_y_4',
            ),
        ),
    ]