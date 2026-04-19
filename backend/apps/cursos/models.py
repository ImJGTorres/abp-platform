from django.conf import settings
from django.db import models


class Curso(models.Model):
    """
    Modelo que representa un curso en el sistema ABP.
    Cada curso puede estar asociado a un período académico.
    """

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    id_periodo_academico = models.ForeignKey(
        'configuracion.PeriodoAcademico',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    usuario_creo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    class Meta:
        db_table = 'curso'

    def __str__(self):
        return self.nombre
