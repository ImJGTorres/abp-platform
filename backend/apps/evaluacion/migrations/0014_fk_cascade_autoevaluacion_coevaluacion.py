"""
Agrega ON DELETE CASCADE a nivel de base de datos en las FK:
  - detalle_autoevaluacion.id_autoevaluacion_id → autoevaluacion.id
  - detalle_coevaluacion.id_coevaluacion_id     → coevaluacion.id

Django maneja el CASCADE en Python por defecto (NO ACTION en la DB),
lo que impide borrar registros directamente desde Supabase/SQL sin pasar
por el ORM. Esta migración alinea la restricción DB con el comportamiento
del modelo.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('evaluacion', '0013_hu028_rubrica_proyecto'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE detalle_autoevaluacion
                DROP CONSTRAINT detalle_autoevaluacion_id_autoevaluacion_id_5472c138_fk;

                ALTER TABLE detalle_autoevaluacion
                ADD CONSTRAINT detalle_autoevaluacion_id_autoevaluacion_id_5472c138_fk
                FOREIGN KEY (id_autoevaluacion_id)
                REFERENCES autoevaluacion(id)
                ON DELETE CASCADE;
            """,
            reverse_sql="""
                ALTER TABLE detalle_autoevaluacion
                DROP CONSTRAINT detalle_autoevaluacion_id_autoevaluacion_id_5472c138_fk;

                ALTER TABLE detalle_autoevaluacion
                ADD CONSTRAINT detalle_autoevaluacion_id_autoevaluacion_id_5472c138_fk
                FOREIGN KEY (id_autoevaluacion_id)
                REFERENCES autoevaluacion(id);
            """,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE detalle_coevaluacion
                DROP CONSTRAINT detalle_coevaluacion_id_coevaluacion_id_01761210_fk;

                ALTER TABLE detalle_coevaluacion
                ADD CONSTRAINT detalle_coevaluacion_id_coevaluacion_id_01761210_fk
                FOREIGN KEY (id_coevaluacion_id)
                REFERENCES coevaluacion(id)
                ON DELETE CASCADE;
            """,
            reverse_sql="""
                ALTER TABLE detalle_coevaluacion
                DROP CONSTRAINT detalle_coevaluacion_id_coevaluacion_id_01761210_fk;

                ALTER TABLE detalle_coevaluacion
                ADD CONSTRAINT detalle_coevaluacion_id_coevaluacion_id_01761210_fk
                FOREIGN KEY (id_coevaluacion_id)
                REFERENCES coevaluacion(id);
            """,
        ),
    ]
