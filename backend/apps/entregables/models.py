import os
import uuid

from django.conf import settings
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
        'cursos.Actividad',
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
    retroalimentacion = models.TextField(null=True, blank=True)
    id_docente_validador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='entregables_validados',
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    numero_version = models.PositiveIntegerField(default=1)
    id_version_anterior = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='versiones_siguientes',
    )

    class Meta:
        db_table = 'entregable'

    def __str__(self):
        return f'{self.titulo} ({self.estado})'


class ArchivoAdjunto(models.Model):
    id_entregable = models.ForeignKey(
        Entregable,
        on_delete=models.PROTECT,
        related_name='archivos',
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archivos_subidos',
    )
    nombre_original = models.CharField(max_length=255)
    nombre_almacenado = models.CharField(max_length=255)
    ruta = models.CharField(max_length=500)
    tipo_mime = models.CharField(max_length=100)
    tamaño_bytes = models.BigIntegerField()
    version = models.PositiveIntegerField(default=1)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'archivo_adjunto'
        ordering = ['-fecha_subida']

    def save(self, *args, **kwargs):
        if not self.pk:
            max_version = ArchivoAdjunto.objects.filter(
                id_entregable=self.id_entregable
            ).aggregate(models.Max('version'))['version__max'] or 0
            self.version = max_version + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nombre_original} (v{self.version})'


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    id_usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo_entregable = models.CharField(max_length=255)
    retroalimentacion = models.TextField(blank=True, default='')
    id_entregable = models.ForeignKey(
        Entregable,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.tipo} — {self.titulo_entregable} → {self.id_usuario_destino_id}'


class EntregableVersion(models.Model):
    id_entregable_original = models.ForeignKey(
        Entregable,
        on_delete=models.CASCADE,
        related_name='hilo_versiones',
    )
    id_version = models.ForeignKey(
        Entregable,
        on_delete=models.CASCADE,
        related_name='registro_version',
    )
    numero_version = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='versiones_creadas',
    )
    motivo_revision = models.TextField(blank=True)

    class Meta:
        db_table = 'entregable_versiones'
        ordering = ['numero_version']

    def __str__(self):
        return f'v{self.numero_version} de entregable {self.id_entregable_original_id}'
