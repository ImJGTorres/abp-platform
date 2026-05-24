from django.db import models


class Alerta(models.Model):
    TIPO_CHOICES = [
        ('actividad_vencida', 'Actividad vencida'),
        ('entregable_pendiente', 'Entregable pendiente'),
        ('entregable_enviado', 'Entregable enviado'),
        ('evaluacion_pendiente', 'Evaluación pendiente'),
        ('bajo_rendimiento', 'Bajo rendimiento'),
    ]
    ESTADO_CHOICES = [
        ('no_leida', 'No leída'),
        ('leida', 'Leída'),
        ('descartada', 'Descartada'),
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
