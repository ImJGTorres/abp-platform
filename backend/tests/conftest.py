import pytest
from rest_framework.test import APIClient
from tests.factories import (
    AdminFactory,
    CursoFactory,
    DocenteFactory,
    PeriodoAcademicoFactory,
    ProyectoFactory,
    UsuarioFactory,
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


# ---------------------------------------------------------------------------
# Fixtures de usuario por rol
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db):
    """Usuario con rol administrador listo para usar en tests."""
    return AdminFactory()


@pytest.fixture
def estudiante_user(db):
    """Usuario con rol estudiante listo para usar en tests.

    Usa UsuarioFactory sin argumentos porque el tipo_rol por defecto
    en UsuarioFactory ya es ESTUDIANTE.
    """
    return UsuarioFactory()


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient autenticado como administrador."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def estudiante_client(api_client, estudiante_user):
    """APIClient autenticado como estudiante."""
    api_client.force_authenticate(user=estudiante_user)
    return api_client


@pytest.fixture
def estudiante_autenticado(db):
    """APIClient con cliente autenticado como estudiante.

    Fixture equivalente a estudiante_client pero retorna un cliente
    independiente. Útil cuando los tests de períodos y otros módulos
    necesitan un cliente de estudiante sin compartir la instancia de api_client.

    UsuarioFactory sin argumentos ya crea un usuario con tipo_rol ESTUDIANTE.
    """
    usuario = UsuarioFactory()
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente
