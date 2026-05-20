from django.conf import settings
from django.db import models


class Exportacion(models.Model):
    TIPO_CHOICES = [
        ('proyecto', 'Reporte de proyecto'),
        ('estudiante', 'Reporte de estudiante'),
        ('equipo', 'Reporte de equipo'),
        ('indicadores', 'Dashboard de indicadores'),
        ('tendencia', 'Tendencia histórica'),
    ]
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    ESTADO_CHOICES = [
        ('generando', 'Generando'),
        ('listo', 'Listo'),
        ('error', 'Error'),
    ]

    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exportaciones',
    )
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_CHOICES)
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES)
    parametros = models.JSONField(default=dict)
    ruta_archivo = models.CharField(max_length=500, blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='generando')
    mensaje_error = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_disponible = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'exportacion'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"{self.tipo_reporte}/{self.formato} [{self.estado}] — usuario {self.id_usuario_id}"
