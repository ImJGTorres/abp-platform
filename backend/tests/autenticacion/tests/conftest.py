import pytest
from django.contrib.auth.hashers import make_password

from apps.usuarios.models import Usuario


@pytest.fixture
def usuario_activo(db):
    return Usuario.objects.create(
        nombre='Prueba',
        apellido='Activo',
        correo='prueba@ufps.edu.co',
        password=make_password('Abcde123!!'),
        tipo_rol=Usuario.TipoRol.ESTUDIANTE,
        estado=Usuario.Estado.ACTIVO,
    )


@pytest.fixture
def usuario_inactivo(db):
    return Usuario.objects.create(
        nombre='Prueba',
        apellido='Inactivo',
        correo='inactivo@ufps.edu.co',
        password=make_password('Abcde123!!'),
        tipo_rol=Usuario.TipoRol.ESTUDIANTE,
        estado=Usuario.Estado.INACTIVO,
    )
