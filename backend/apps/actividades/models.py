from django.db import models


class FaseProyecto(models.Model):
    nombre = models.CharField(max_length=200)
    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        related_name='fases',
    )

    class Meta:
        db_table = 'fase_proyecto'

    def __str__(self):
        return f'{self.nombre} ({self.id_proyecto})'


class Actividad(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    fecha_limite = models.DateField(null=True, blank=True)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    id_fase = models.ForeignKey(
        FaseProyecto,
        on_delete=models.CASCADE,
        related_name='actividades',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'actividad'

    def __str__(self):
        return self.nombre
