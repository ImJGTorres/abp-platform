from django.db import models


class Alerta(models.Model):
    TIPO_CHOICES = [
        ('actividad_vencida', 'Actividad vencida'),
        ('entregable_pendiente', 'Entregable pendiente'),
        ('entregable_enviado', 'Entregable enviado'),
        ('evaluacion_pendiente', 'Evaluación pendiente'),
        ('bajo_rendimiento', 'Bajo rendimiento'),
        ('recordatorio_vencimiento', 'Recordatorio de vencimiento'),
    ]
    ESTADO_CHOICES = [
        ('no_leida', 'No leída'),
        ('leida', 'Leída'),
        ('descartada', 'Descartada'),
    ]
    GRAVEDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]

    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    id_usuario_destino = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='alertas',
        db_column='id_usuario_destino_id',
    )
    id_proyecto = models.ForeignKey(
        'cursos.Proyecto',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas',
        db_column='id_proyecto_id',
    )
    mensaje = models.TextField()
    gravedad = models.CharField(max_length=10, choices=GRAVEDAD_CHOICES, default='media')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='no_leida')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    referencia_id = models.BigIntegerField(
        null=True, blank=True,
        help_text='ID del objeto origen (actividad o entregable)'
    )

    class Meta:
        db_table = 'alerta'
        ordering = ['-fecha_generacion']
        constraints = [
            models.UniqueConstraint(
                fields=['tipo', 'id_usuario_destino', 'referencia_id'],
                name='unique_alerta_por_usuario_referencia',
            )
        ]

    def __str__(self):
        return f"[{self.tipo}] → {self.id_usuario_destino_id} ({self.estado})"


class ColaCorreo(models.Model):
    PLANTILLA_CHOICES = [
        ('alerta', 'Alerta'),
        ('anuncio', 'Anuncio'),
        ('calificacion', 'Calificación'),
        ('recordatorio', 'Recordatorio'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
    ]

    id_usuario_destino = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='correos_encolados',
        db_column='id_usuario_destino_id',
    )
    asunto = models.CharField(max_length=255)
    plantilla = models.CharField(max_length=20, choices=PLANTILLA_CHOICES)
    contexto = models.JSONField(default=dict, blank=True)
    estado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default='pendiente', db_index=True
    )
    intentos = models.IntegerField(default=0)
    error = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cola_correo'
        ordering = ['fecha_creacion']

    def __str__(self):
        return f"[{self.plantilla}] → {self.id_usuario_destino_id} ({self.estado})"
