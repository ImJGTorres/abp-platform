from django.db import models


class Entregable(models.Model):
    TIPO_CHOICES = [
        ('documento', 'Documento'),
        ('prototipo', 'Prototipo'),
        ('codigo', 'Código'),
        ('presentacion', 'Presentación'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    id_actividad = models.ForeignKey(
        'actividades.Actividad',
        on_delete=models.PROTECT,
        related_name='entregables',
    )
    id_equipo = models.ForeignKey(
        'equipos.Equipo',
        on_delete=models.PROTECT,
        related_name='entregables',
    )
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'entregable'

    def __str__(self):
        return f'{self.titulo} ({self.estado})'
