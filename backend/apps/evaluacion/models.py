from django.db import models


class Rubrica(models.Model):
    class Meta:
        db_table = 'rubrica'


class CriterioRubrica(models.Model):
    id_rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='criterios',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    peso = models.DecimalField(max_digits=5, decimal_places=2)
    rap = models.ForeignKey(
        'cursos.ResultadoAprendizaje',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='criterios',
    )

    class Meta:
        db_table = 'criterio_rubrica'
