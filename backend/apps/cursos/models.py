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


class HitoProyecto(models.Model):

    class Tipo(models.TextChoices):
        HITO = 'hito', 'Hito'
        ENTREGA = 'entrega', 'Entrega'
        REVISION = 'revision', 'Revisión'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROGRESO = 'en_progreso', 'En Progreso'
        COMPLETADO = 'completado', 'Completado'
        CANCELADO = 'cancelado', 'Cancelado'

    id_proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='hitos',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.HITO)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hito_proyecto'
        ordering = ['fecha_inicio', 'fecha_fin']

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()}) — {self.id_proyecto}'


class CursoEstudiante(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='estudiantes')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cursos_inscritos')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')

    class Meta:
        db_table = 'curso_estudiante'
        unique_together = ('curso', 'estudiante')
        managed = False

    def __str__(self):
        return f'{self.estudiante} en {self.curso}'


class FaseProyecto(models.Model):

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROGRESO = 'en_progreso', 'En Progreso'
        COMPLETADA = 'completada', 'Completada'

    id_proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='fases',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    orden = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    porcentaje_completado = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'fase_proyecto'
        constraints = [
            models.UniqueConstraint(
                fields=['id_proyecto', 'orden'],
                name='unique_orden_por_fase_proyecto',
            )
        ]
        ordering = ['orden']

    def __str__(self):
        return f'Fase {self.orden}: {self.nombre} — {self.id_proyecto}'


class Actividad(models.Model):

    class Prioridad(models.TextChoices):
        ALTA = 'alta', 'Alta'
        MEDIA = 'media', 'Media'
        BAJA = 'baja', 'Baja'

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROGRESO = 'en_progreso', 'En Progreso'
        COMPLETADA = 'completada', 'Completada'
        BLOQUEADA = 'bloqueada', 'Bloqueada'

    id_fase = models.ForeignKey(
        FaseProyecto,
        on_delete=models.CASCADE,
        related_name='actividades',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    fecha_limite = models.DateField()
    prioridad = models.CharField(
        max_length=5,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
    )
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    id_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_responsable',
    )
    id_equipo_asignado = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades',
    )
    responsables = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='actividades_asignadas',
        blank=True,
    )

    class Meta:
        db_table = 'actividad'
        ordering = ['fecha_limite', 'prioridad']

    def __str__(self):
        return f'{self.nombre} [{self.get_prioridad_display()}] — {self.id_fase}'


class ActividadDependencia(models.Model):
    """Relación de precedencia entre actividades (grafo dirigido acíclico)."""

    id_actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='dependencias',
    )
    id_actividad_predecesor = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='sucesores',
    )

    class Meta:
        db_table = 'actividad_depende_de'
        constraints = [
            models.UniqueConstraint(
                fields=['id_actividad', 'id_actividad_predecesor'],
                name='unique_dependencia_actividad',
            ),
            models.CheckConstraint(
                check=~models.Q(id_actividad=models.F('id_actividad_predecesor')),
                name='no_autoref_dependencia',
            ),
        ]

    def __str__(self):
        return f'Actividad {self.id_actividad_id} depende de {self.id_actividad_predecesor_id}'


class AvanceActividad(models.Model):

    class Tipo(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        ENLACE = 'enlace', 'Enlace'

    id_actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='avances',
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='avances_registrados',
    )
    descripcion = models.TextField()
    porcentaje_completado = models.PositiveSmallIntegerField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(
        max_length=6,
        choices=Tipo.choices,
        default=Tipo.TEXTO,
    )
    url_referencia = models.URLField(null=True, blank=True)

    class Meta:
        db_table = 'avance_actividad'
        ordering = ['-fecha_registro']
        constraints = [
            models.CheckConstraint(
                check=models.Q(porcentaje_completado__gte=0) & models.Q(porcentaje_completado__lte=100),
                name='avance_porcentaje_0_100',
            )
        ]

    def __str__(self):
        return f'Avance {self.porcentaje_completado}% — {self.id_actividad} por {self.id_usuario}'


class ResultadoAprendizaje(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='raps',
    )
    nombre = models.CharField(max_length=50, default='')
    descripcion = models.TextField()
    competencia_asociada = models.CharField(max_length=200, null=True, blank=True)
    porcentaje_evaluacion = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'resultado_aprendizaje'
        ordering = ['id']

    def __str__(self):
        return f'{self.nombre} – {self.descripcion[:50]}'
