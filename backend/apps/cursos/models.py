from django.conf import settings
from django.db import models


class Curso(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        ACTIVO = 'activo', 'Activo'
        CERRADO = 'cerrado', 'Cerrado'

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    codigo = models.CharField(max_length=20)
    id_docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cursos_docente',
    )
    id_periodo_academico = models.ForeignKey(
        'configuracion.PeriodoAcademico',
        on_delete=models.PROTECT,
    )
    usuario_creo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='cursos_creados',
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'curso'
        constraints = [
            models.UniqueConstraint(
                fields=['codigo', 'id_periodo_academico'],
                name='unique_codigo_por_periodo',
            )
        ]

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Proyecto(models.Model):

    class Estado(models.TextChoices):
        PLANIFICADO = 'planificado', 'Planificado'
        EN_EJECUCION = 'en_ejecucion', 'En Ejecución'
        FINALIZADO = 'finalizado', 'Finalizado'

    id_curso = models.OneToOneField(
        Curso,
        on_delete=models.PROTECT,
        related_name='proyecto',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PLANIFICADO,
    )
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'proyecto'

    def __str__(self):
        return f'{self.nombre} ({self.id_curso})'
