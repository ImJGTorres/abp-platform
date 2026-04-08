from django.db import models

class Usuario(models.Model):

    class TipoRol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        DIRECTOR      = 'director',      'Director'
        DOCENTE       = 'docente',       'Docente'
        LIDER_EQUIPO  = 'lider_equipo',  'Líder de Equipo'
        ESTUDIANTE    = 'estudiante',    'Estudiante'

    class Estado(models.TextChoices):
        ACTIVO   = 'activo',   'Activo'
        INACTIVO = 'inactivo', 'Inactivo'

    nombre              = models.CharField(max_length=100)
    apellido            = models.CharField(max_length=100)
    correo              = models.EmailField(max_length=150, unique=True)
    contrasena_hash     = models.CharField(max_length=255)
    telefono            = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil         = models.CharField(max_length=500, blank=True, null=True)
    tipo_rol            = models.CharField(max_length=20, choices=TipoRol.choices)
    estado              = models.CharField(max_length=10, choices=Estado.choices,
                                           default=Estado.ACTIVO)
    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.correo})'