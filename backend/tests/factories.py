import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.hashers import make_password, check_password
from apps.usuarios.models import Usuario

class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = Usuario

    nombre          = factory.Sequence(lambda n: f"Usuario{n}")
    apellido        = factory.Sequence(lambda n: f"Apellido{n}")
    correo          = factory.Sequence(lambda n: f"usuario{n}@ufps.edu.co")
    contrasena_hash = factory.LazyFunction(lambda: make_password("Abc123!"))
    tipo_rol        = Usuario.TipoRol.ESTUDIANTE
    estado          = Usuario.Estado.ACTIVO

class AdminFactory(UsuarioFactory):
    correo   = factory.Sequence(lambda n: f"admin{n}@ufps.edu.co")
    tipo_rol = Usuario.TipoRol.ADMINISTRADOR

