from django.conf import settings
from django.db import models


class Rubrica(models.Model):

    class Tipo(models.TextChoices):
        ENTREGABLE   = 'entregable',   'Entregable'
        PROCESO      = 'proceso',      'Proceso'
        PRESENTACION = 'presentacion', 'Presentación'

    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rubricas',
    )
    id_docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rubricas_creadas',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.CharField(
        max_length=12,
        choices=Tipo.choices,
        default=Tipo.ENTREGABLE,
    )
    peso_total = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rubrica'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'


class CriterioRubrica(models.Model):

    id_rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.CASCADE,
        related_name='criterios',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(null=True, blank=True)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2)
    id_rap = models.ForeignKey(
        'cursos.ResultadoAprendizaje',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='criterios_rubrica',
    )

    class Meta:
        db_table = 'criterio_rubrica'
        ordering = ['id']

    def __str__(self):
        return f'{self.nombre} ({self.peso_porcentual}%) — {self.id_rubrica}'


class NivelDesempeno(models.Model):

    class Etiqueta(models.TextChoices):
        INSUFICIENTE  = 'insuficiente',  'Insuficiente'
        BASICO        = 'basico',        'Básico'
        SATISFACTORIO = 'satisfactorio', 'Satisfactorio'
        EXCELENTE     = 'excelente',     'Excelente'

    id_criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.CASCADE,
        related_name='niveles',
    )
    nivel = models.PositiveSmallIntegerField()
    etiqueta = models.CharField(
        max_length=13,
        choices=Etiqueta.choices,
    )
    descripcion = models.TextField()
    puntos = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'nivel_desempeno'
        ordering = ['nivel']
        constraints = [
            models.UniqueConstraint(
                fields=['id_criterio', 'nivel'],
                name='unique_nivel_por_criterio',
            ),
            models.CheckConstraint(
                check=models.Q(nivel__gte=1) & models.Q(nivel__lte=4),
                name='nivel_entre_1_y_4',
            ),
        ]

    def __str__(self):
        return f'Nivel {self.nivel} ({self.get_etiqueta_display()}) — {self.id_criterio}'


# ---------------------------------------------------------------------------
# HU-24: Evaluacion de entregables
# ---------------------------------------------------------------------------

class Evaluacion(models.Model):

    class Estado(models.TextChoices):
        BORRADOR  = 'borrador',  'Borrador'
        PUBLICADA = 'publicada', 'Publicada'

    id_entregable = models.ForeignKey(
        'entregables.Entregable',
        on_delete=models.PROTECT,
        related_name='evaluaciones',
    )
    id_rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.PROTECT,
        related_name='evaluaciones',
    )
    id_docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluaciones_realizadas',
    )
    puntuacion_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    comentario_general = models.TextField(null=True, blank=True)
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )

    class Meta:
        db_table = 'evaluacion'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'Evaluación {self.pk} — {self.id_entregable} [{self.get_estado_display()}]'


class CalificacionCriterio(models.Model):

    id_evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='calificaciones',
    )
    id_criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.PROTECT,
        related_name='calificaciones',
    )
    id_nivel_seleccionado = models.ForeignKey(
        NivelDesempeno,
        on_delete=models.PROTECT,
        related_name='calificaciones',
    )
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=2)
    comentario_criterio = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'calificacion_criterio'
        constraints = [
            models.UniqueConstraint(
                fields=['id_evaluacion', 'id_criterio'],
                name='unique_criterio_por_evaluacion',
            )
        ]

    def __str__(self):
        return (
            f'Criterio {self.id_criterio_id} → nivel {self.id_nivel_seleccionado_id} '
            f'({self.puntos_obtenidos} pts) — evaluación {self.id_evaluacion_id}'
        )


# ---------------------------------------------------------------------------
# HU-25: Retroalimentación
# ---------------------------------------------------------------------------

class Retroalimentacion(models.Model):

    class Tipo(models.TextChoices):
        GRUPAL     = 'grupal',     'Grupal'
        INDIVIDUAL = 'individual', 'Individual'
        ACTIVIDAD  = 'actividad',  'Actividad'

    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='retroalimentaciones',
    )
    id_docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retroalimentaciones_dadas',
    )
    # Destino de la retroalimentación — solo uno debe estar presente según el tipo.
    id_equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retroalimentaciones',
    )
    id_estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retroalimentaciones_recibidas',
    )
    id_actividad = models.ForeignKey(
        'cursos.Actividad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retroalimentaciones',
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    contenido = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'retroalimentacion'
        ordering = ['-fecha_registro']
        constraints = [
            # grupal  → id_equipo no nulo
            models.CheckConstraint(
                check=(
                    models.Q(tipo='grupal',     id_equipo__isnull=False) |
                    models.Q(tipo='individual', id_estudiante__isnull=False) |
                    models.Q(tipo='actividad',  id_actividad__isnull=False)
                ),
                name='retro_tipo_fk_consistente',
            )
        ]

    def __str__(self):
        return f'[{self.get_tipo_display()}] Retroalimentación {self.pk} — proyecto {self.id_proyecto_id}'


# ---------------------------------------------------------------------------
# HU-26: Autoevaluación
# ---------------------------------------------------------------------------

class Autoevaluacion(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        ENVIADA  = 'enviada',  'Enviada'

    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='autoevaluaciones',
    )
    id_estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='autoevaluaciones',
    )
    id_rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.PROTECT,
        related_name='autoevaluaciones',
    )
    puntuacion_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    reflexion_texto = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    # Identificador del periodo de evaluación (ej. "2026-1", "2026-S2").
    periodo_evaluacion = models.CharField(max_length=50)

    class Meta:
        db_table = 'autoevaluacion'
        ordering = ['-fecha_registro']
        constraints = [
            # BD02 — un estudiante solo puede autoevaluarse una vez por periodo en un proyecto.
            models.UniqueConstraint(
                fields=['id_proyecto', 'id_estudiante', 'periodo_evaluacion'],
                name='unique_autoevaluacion_por_periodo',
            )
        ]

    def __str__(self):
        return (
            f'Autoevaluación {self.pk} — {self.id_estudiante_id} '
            f'[{self.periodo_evaluacion}] [{self.get_estado_display()}]'
        )


class DetalleAutoevaluacion(models.Model):
    """Nivel de desempeño seleccionado por el estudiante para cada criterio de la rúbrica."""

    id_autoevaluacion = models.ForeignKey(
        Autoevaluacion,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    id_criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.PROTECT,
        related_name='autoevaluaciones',
    )
    id_nivel_seleccionado = models.ForeignKey(
        NivelDesempeno,
        on_delete=models.PROTECT,
        related_name='autoevaluaciones',
    )
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=2)
    comentario = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'detalle_autoevaluacion'
        constraints = [
            models.UniqueConstraint(
                fields=['id_autoevaluacion', 'id_criterio'],
                name='unique_criterio_por_autoevaluacion',
            )
        ]

    def __str__(self):
        return (
            f'Criterio {self.id_criterio_id} → nivel {self.id_nivel_seleccionado_id} '
            f'({self.puntos_obtenidos} pts) — autoevaluación {self.id_autoevaluacion_id}'
        )


# ---------------------------------------------------------------------------
# HU-27: Coevaluación
# ---------------------------------------------------------------------------

class Coevaluacion(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        ENVIADA  = 'enviada',  'Enviada'

    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='coevaluaciones',
    )
    id_evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coevaluaciones_realizadas',
    )
    id_evaluado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coevaluaciones_recibidas',
    )
    id_rubrica = models.ForeignKey(
        Rubrica,
        on_delete=models.PROTECT,
        related_name='coevaluaciones',
    )
    puntuacion_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    comentario = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    periodo_evaluacion = models.CharField(max_length=50)

    class Meta:
        db_table = 'coevaluacion'
        ordering = ['-fecha_registro']
        constraints = [
            models.UniqueConstraint(
                fields=['id_evaluador', 'id_evaluado', 'periodo_evaluacion'],
                name='unique_coevaluacion_por_periodo',
            ),
            models.CheckConstraint(
                check=~models.Q(id_evaluador=models.F('id_evaluado')),
                name='evaluador_distinto_de_evaluado',
            ),
        ]

    def __str__(self):
        return (
            f'Coevaluación {self.pk} — {self.id_evaluador_id} → {self.id_evaluado_id} '
            f'[{self.periodo_evaluacion}]'
        )


class DetalleCoevaluacion(models.Model):

    id_coevaluacion = models.ForeignKey(
        Coevaluacion,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    id_criterio = models.ForeignKey(
        CriterioRubrica,
        on_delete=models.PROTECT,
        related_name='coevaluaciones',
    )
    id_nivel_seleccionado = models.ForeignKey(
        NivelDesempeno,
        on_delete=models.PROTECT,
        related_name='coevaluaciones',
    )
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=2)
    comentario = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'detalle_coevaluacion'
        constraints = [
            models.UniqueConstraint(
                fields=['id_coevaluacion', 'id_criterio'],
                name='unique_criterio_por_coevaluacion',
            )
        ]

    def __str__(self):
        return (
            f'Criterio {self.id_criterio_id} → nivel {self.id_nivel_seleccionado_id} '
            f'({self.puntos_obtenidos} pts) — coevaluación {self.id_coevaluacion_id}'
        )