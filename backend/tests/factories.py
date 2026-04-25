import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import date
from apps.usuarios.models import Usuario
from apps.roles.models import Rol, Permiso
from apps.cursos.models import Curso, Proyecto
from apps.configuracion.models import PeriodoAcademico

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


class DocenteFactory(DjangoModelFactory):
    class Meta:
        model = Usuario

    correo = factory.Sequence(lambda n: f"docente{n}@ufps.edu.co")
    nombre = "Docente Test"
    tipo_rol = Usuario.TipoRol.DOCENTE
    estado = Usuario.Estado.ACTIVO
    password = factory.LazyFunction(lambda: make_password("Abc123!"))


class PeriodoAcademicoFactory(DjangoModelFactory):
    class Meta:
        model = PeriodoAcademico

    nombre = factory.Sequence(lambda n: f"Periodo {n}")
    fecha_inicio = date(2026, 1, 1)
    fecha_fin = date(2026, 6, 30)
    estado = PeriodoAcademico.Estado.ACTIVO
    usuario_creo = factory.SubFactory(DocenteFactory)


class CursoFactory(DjangoModelFactory):
    class Meta:
        model = Curso

    nombre = "Ingeniería de Software I"
    codigo = factory.Sequence(lambda n: f"IS-{n:03d}")
    id_docente = factory.SubFactory(DocenteFactory)
    id_periodo_academico = factory.SubFactory(PeriodoAcademicoFactory)
    usuario_creo = factory.SelfAttribute('id_docente')
    estado = Curso.Estado.ACTIVO


class ProyectoFactory(DjangoModelFactory):
    class Meta:
        model = Proyecto

    id_curso = factory.SubFactory(CursoFactory)
    nombre = "Proyecto Test"
    fecha_inicio = date(2026, 2, 1)
    fecha_fin_estimada = date(2026, 5, 31)
    estado = Proyecto.Estado.PLANIFICADO