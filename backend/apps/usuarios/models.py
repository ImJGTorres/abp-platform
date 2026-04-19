# AbstractBaseUser: clase base de Django para modelos de autenticación personalizados.
# Aporta el campo 'password', y los métodos set_password() y check_password().
# BaseUserManager: clase base para el manager (UsuarioManager) que crea instancias del modelo.
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from apps.roles.models import Rol


# UsuarioManager: reemplaza al manager por defecto (models.Manager).
# Django lo exige cuando se usa AbstractBaseUser, porque necesita saber
# cómo construir una instancia del modelo de forma segura (hasheando la contraseña).
class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El correo es obligatorio.')
        # normalize_email estandariza el dominio a minúsculas (ej. User@GMAIL.COM → User@gmail.com)
        correo = self.normalize_email(correo)
        # self.model construye una instancia del modelo asociado a este manager (Usuario)
        usuario = self.model(correo=correo, **extra_fields)
        # set_password hashea la contraseña y la guarda en el campo 'password'
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario


# AbstractBaseUser: le dice a Django que esta clase ES el modelo de autenticación.
# Esto satisface el contrato que exige AUTH_USER_MODEL = 'usuarios.Usuario' en settings.py.
# Sin esta herencia Django no sabe cómo manejar contraseñas ni sesiones para este modelo.
class Usuario(AbstractBaseUser):

    class TipoRol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        DIRECTOR      = 'director',      'Director'
        DOCENTE       = 'docente',       'Docente'
        LIDER_EQUIPO  = 'lider_equipo',  'Líder de Equipo'
        ESTUDIANTE    = 'estudiante',    'Estudiante'

    class Estado(models.TextChoices):
        ACTIVO   = 'activo',   'Activo'
        INACTIVO = 'inactivo', 'Inactivo'

    # Nota: ya no se declara 'contrasena_hash' aquí.
    # AbstractBaseUser agrega automáticamente el campo 'password' a la tabla,
    # que cumple exactamente esa función. La migración 0003 renombró la columna.
    nombre              = models.CharField(max_length=100)
    apellido            = models.CharField(max_length=100)
    correo              = models.EmailField(max_length=150, unique=True)
    telefono            = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil         = models.CharField(max_length=500, blank=True, null=True)
    tipo_rol            = models.CharField(max_length=20, choices=TipoRol.choices)
    estado              = models.CharField(max_length=10, choices=Estado.choices,
                                           default=Estado.ACTIVO)
    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Conecta el modelo con su manager personalizado.
    # A partir de aquí, Usuario.objects.create_user(...) usa UsuarioManager.
    objects = UsuarioManager()

    # USERNAME_FIELD: le indica a Django qué campo usar como identificador único
    # para autenticarse (equivalente al 'username' en el modelo estándar de Django).
    # En este proyecto el identificador es el correo electrónico.
    USERNAME_FIELD  = 'correo'

    # REQUIRED_FIELDS: lista de campos adicionales que se piden al crear un superusuario
    # por consola (manage.py createsuperuser). Lista vacía porque solo se requiere el correo.
    # Django lanzaba AttributeError al arrancar porque este atributo no existía antes.
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.correo})'

class UsuarioRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='roles')
    rol     = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios')

    class Meta:
        db_table = 'usuario_rol'
        unique_together = ('usuario', 'rol')

    def __str__(self):
        return f'{self.usuario.correo} → {self.rol.nombre}'