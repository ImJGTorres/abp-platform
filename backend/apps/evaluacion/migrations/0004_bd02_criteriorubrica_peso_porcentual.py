"""
BD02 – Diseñar tabla de criterios de rúbrica.

Ajustes sobre criterio_rubrica:
  - Renombra `peso` → `peso_porcentual` para reflejar su naturaleza porcentual.
  - Cambia `rap` → `id_rap` alineando la convención de nomenclatura de FKs.
  - Hace `descripcion` nullable para consistencia con el resto del esquema.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0003_bd01_rubrica_campos'),
        ('cursos', '0023_fix_usuario_fk_set_null'),
    ]

    operations = [
        migrations.RenameField(
            model_name='criteriorubrica',
            old_name='peso',
            new_name='peso_porcentual',
        ),
        migrations.RenameField(
            model_name='criteriorubrica',
            old_name='rap',
            new_name='id_rap',
        ),
        migrations.AlterField(
            model_name='criteriorubrica',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='criteriorubrica',
            name='id_rap',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='criterios_rubrica',
                to='cursos.resultadoaprendizaje',
            ),
        ),
        migrations.AlterModelOptions(
            name='criteriorubrica',
            options={'ordering': ['id']},
        ),
    ]