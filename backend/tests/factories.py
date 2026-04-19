import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.hashers import make_password, check_password
from apps.usuarios.models import Usuario
from apps.roles.models import Rol, Permiso

class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = Usuario

    nombre          = factory.Sequence(lambda n: f"Usuario{n}")
    apellido        = factory.Sequence(lambda n: f"Apellido{n}")
    correo          = factory.Sequence(lambda n: f"usuario{n}@ufps.edu.co")
    password = factory.LazyFunction(lambda: make_password("Abc123!"))
    tipo_rol        = Usuario.TipoRol.ESTUDIANTE
    estado          = Usuario.Estado.ACTIVO

class AdminFactory(UsuarioFactory):
    correo   = factory.Sequence(lambda n: f"admin{n}@ufps.edu.co")
    tipo_rol = Usuario.TipoRol.ADMINISTRADOR

class UsuarioInactivoFactory(UsuarioFactory):
    correo  = factory.Sequence(lambda n: f"inactivo{n}@ufps.edu.co")
    estado  = Usuario.Estado.INACTIVO

class RolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rol

    nombre = factory.Sequence(lambda n: f"Rol_{n}")
    descripcion = factory.Faker("sentence")
    estado = "activo"


class PermisoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permiso

    codigo = factory.Sequence(lambda n: f"permiso_{n}")
    modulo = factory.Faker("word")
    descripcion = factory.Faker("sentence")