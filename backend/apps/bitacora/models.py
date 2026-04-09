from django.db import models


class BitacoraQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError('BitacoraSistema es append-only: no se permite UPDATE.')

    def delete(self):
        raise TypeError('BitacoraSistema es append-only: no se permite DELETE.')


class BitacoraManager(models.Manager):
    def get_queryset(self):
        return BitacoraQuerySet(self.model, using=self._db)


class BitacoraSistema(models.Model):

    class Accion(models.TextChoices):
        CREATE         = 'CREATE',        'Crear'
        UPDATE         = 'UPDATE',        'Actualizar'
        DELETE         = 'DELETE',        'Eliminar'
        LOGIN          = 'LOGIN',         'Inicio de sesión'
        LOGOUT         = 'LOGOUT',        'Cierre de sesión'
        ACCESS_DENIED  = 'ACCESS_DENIED', 'Acceso denegado'
        ACCESS         = 'ACCESS',        'Consulta'

    id_usuario     = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_usuario',
    )
    nombre_usuario = models.CharField(max_length=255)
    accion         = models.CharField(max_length=50, choices=Accion.choices)
    modulo         = models.CharField(max_length=100)
    descripcion    = models.TextField(null=True, blank=True)
    ip_origen      = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora     = models.DateTimeField(auto_now_add=True)

    objects = BitacoraManager()

    class Meta:
        db_table = 'bitacora_sistema'
        indexes = [
            models.Index(fields=['id_usuario'],  name='idx_bitacora_usuario'),
            models.Index(fields=['-fecha_hora'], name='idx_bitacora_fecha'),
            models.Index(fields=['modulo'],      name='idx_bitacora_modulo'),
            models.Index(fields=['accion'],      name='idx_bitacora_accion'),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise TypeError('BitacoraSistema es append-only: no se permite modificar un registro existente.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError('BitacoraSistema es append-only: no se permite DELETE.')

    def __str__(self):
        return f'[{self.fecha_hora}] {self.accion} - {self.nombre_usuario} ({self.modulo})'