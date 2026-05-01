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
    cantidad_max_estudiantes = models.PositiveIntegerField(default=30)
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

    id_curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='proyectos',
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


class ObjetivoProyecto(models.Model):
    """
    Objetivo asociado a un proyecto (general o específico).

    Cada proyecto puede tener varios objetivos; el campo `orden` define
    el orden de presentación dentro del proyecto y debe ser único por proyecto.
    Los objetivos se pueden crear en lote desde el serializador.
    """

    class Tipo(models.TextChoices):
        # Objetivo de alto nivel que describe el propósito global del proyecto.
        GENERAL    = 'general',    'General'
        # Objetivo concreto y medible derivado del objetivo general.
        ESPECIFICO = 'especifico', 'Específico'

    # FK al proyecto dueño; al borrar el proyecto se borran sus objetivos (CASCADE).
    id_proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='objetivos',
    )

    # Texto libre que describe el objetivo.
    descripcion = models.TextField()

    # Clasifica el objetivo como general o específico.
    tipo = models.CharField(
        max_length=10,
        choices=Tipo.choices,
    )

    # Posición del objetivo dentro del proyecto (1-based).
    # Único por proyecto para garantizar un orden sin huecos.
    orden = models.PositiveIntegerField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'objetivo_proyecto'
        # Un número de orden solo puede aparecer una vez por proyecto.
        constraints = [
            models.UniqueConstraint(
                fields=['id_proyecto', 'orden'],
                name='unique_orden_por_proyecto',
            )
        ]
        # Orden por defecto al consultar: primero generales, luego específicos,
        # dentro de cada tipo por posición ascendente.
        ordering = ['tipo', 'orden']

    def __str__(self):
        return f'[{self.get_tipo_display()}] Objetivo {self.orden} — {self.id_proyecto}'
