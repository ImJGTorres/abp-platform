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

