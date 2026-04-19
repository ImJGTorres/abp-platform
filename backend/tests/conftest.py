import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import UsuarioFactory, AdminFactory
from apps.usuarios.models import Usuario

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return AdminFactory()

@pytest.fixture
def estudiante_user(db):
    return UsuarioFactory(tipo_rol=Usuario.TipoRol.ESTUDIANTE)

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def estudiante_client(api_client, estudiante_user):
    api_client.force_authenticate(user=estudiante_user)
    return api_client

from tests.factories import UsuarioInactivoFactory
@pytest.fixture
def usuario_activo(db):
    from django.contrib.auth.hashers import make_password
    return UsuarioFactory(
        correo          = "prueba@ufps.edu.co",
        password = make_password("Abc123!!")
    )

@pytest.fixture
def usuario_inactivo(db):
    from django.contrib.auth.hashers import make_password
    return UsuarioInactivoFactory(
        correo          = "inactivo@ufps.edu.co",
        password = make_password("Abc123!!")
    )
