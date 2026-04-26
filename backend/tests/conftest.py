import pytest
from rest_framework.test import APIClient
from tests.factories import (
    DocenteFactory,
    PeriodoAcademicoFactory,
    CursoFactory,
    ProyectoFactory,
    UsuarioFactory,
    AdminFactory,
)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def docente_a():
    return DocenteFactory()

@pytest.fixture
def docente_b():
    return DocenteFactory()

@pytest.fixture
def periodo_activo(docente_a):
    return PeriodoAcademicoFactory(usuario_creo=docente_a)

@pytest.fixture
def cliente_a(api_client, docente_a):
    api_client.force_authenticate(user=docente_a)
    return api_client

@pytest.fixture
def cliente_b(api_client, docente_b):
    client = APIClient()
    client.force_authenticate(user=docente_b)
    return client

# Existing fixtures (kept)
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
