import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# -------------------------------------------------------
# FIXTURES
# -------------------------------------------------------
@pytest.fixture
def cliente():
    return APIClient()

@pytest.fixture
def admin_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    usuario = Usuario.objects.create(
        nombre="Admin",
        apellido="Test",
        correo="admin@test.com",
        contrasena_hash=make_password("admin123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def docente_autenticado(db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    cliente = APIClient()
    usuario = Usuario.objects.create(
        nombre="Docente",
        apellido="Test",
        correo="docente@test.com",
        contrasena_hash=make_password("doc123"),
        tipo_rol=Usuario.TipoRol.DOCENTE,
        estado=Usuario.Estado.ACTIVO
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def estudiante_autenticado(db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    cliente = APIClient()
    usuario = Usuario.objects.create(
        nombre="Estudiante",
        apellido="Test",
        correo="estudiante@test.com",
        contrasena_hash=make_password("est123"),
        tipo_rol=Usuario.TipoRol.ESTUDIANTE,
        estado=Usuario.Estado.ACTIVO
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def evento_base(db):
    """Crea un evento de prueba en la bitácora"""
    from apps.bitacora.utils import registrar_evento
    from apps.bitacora.models import BitacoraSistema
    from django.test import RequestFactory
    factory = RequestFactory()
    request = factory.get('/test')
    request.usuario = None
    registrar_evento(
        request,
        accion=BitacoraSistema.Accion.ACCESS,
        modulo='configuracion',
        descripcion='Test de acceso'
    )

# -------------------------------------------------------
# CP-01: Acción de usuario queda registrada automáticamente
# -------------------------------------------------------
@pytest.mark.django_db
def test_registrar_evento_crea_registro(evento_base):
    """Verifica que registrar_evento() guarda en la BD"""
    from apps.bitacora.models import BitacoraSistema
    assert BitacoraSistema.objects.exists()
    evento = BitacoraSistema.objects.first()
    assert evento.accion == 'ACCESS'
    assert evento.modulo == 'configuracion'

# -------------------------------------------------------
# CP-02: GET /api/bitacora/ retorna lista de eventos
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint GET /api/bitacora/ no implementado")
@pytest.mark.django_db
def test_listar_eventos_como_admin(admin_autenticado, evento_base):
    url = reverse("bitacora-list")
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK
    assert len(respuesta.data) > 0

# -------------------------------------------------------
# CP-03: GET /api/bitacora/ como docente retorna 403
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_listar_eventos_como_docente(docente_autenticado):
    url = reverse("bitacora-list")
    respuesta = docente_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN

# -------------------------------------------------------
# CP-04: GET /api/bitacora/ como estudiante retorna 403
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_listar_eventos_como_estudiante(estudiante_autenticado):
    url = reverse("bitacora-list")
    respuesta = estudiante_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN

# -------------------------------------------------------
# CP-05: Registro existente no puede ser modificado (append-only)
# -------------------------------------------------------
@pytest.mark.django_db
def test_bitacora_rechaza_update(evento_base):
    """Verifica que el modelo rechaza UPDATE"""
    from apps.bitacora.models import BitacoraSistema
    from django.db import DatabaseError
    evento = BitacoraSistema.objects.first()
    with pytest.raises((TypeError, DatabaseError)):
        evento.descripcion = "Intento de cambio"
        evento.save()

# -------------------------------------------------------
# CP-06: Registro existente no puede ser eliminado (append-only)
# -------------------------------------------------------
@pytest.mark.django_db
def test_bitacora_rechaza_delete(evento_base):
    """Verifica que el modelo rechaza DELETE"""
    from apps.bitacora.models import BitacoraSistema
    evento = BitacoraSistema.objects.first()
    with pytest.raises(TypeError):
        evento.delete()

# -------------------------------------------------------
# CP-07: Filtrar eventos por usuario
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_filtrar_eventos_por_usuario(admin_autenticado, evento_base):
    url = reverse("bitacora-list") + "?usuario=admin@test.com"
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK

# -------------------------------------------------------
# CP-08: Filtrar eventos por módulo
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_filtrar_eventos_por_modulo(admin_autenticado, evento_base):
    url = reverse("bitacora-list") + "?modulo=configuracion"
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK

# -------------------------------------------------------
# CP-09: Filtrar eventos por rango de fechas
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_filtrar_eventos_por_fecha(admin_autenticado, evento_base):
    url = reverse("bitacora-list") + "?fecha_inicio=2026-01-01&fecha_fin=2026-12-31"
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK

# -------------------------------------------------------
# CP-10: Cada registro contiene campos mínimos requeridos
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Endpoint no implementado")
@pytest.mark.django_db
def test_registro_contiene_campos_minimos(admin_autenticado, evento_base):
    url = reverse("bitacora-list")
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK
    registro = respuesta.data[0]
    assert 'nombre_usuario' in registro
    assert 'accion' in registro
    assert 'modulo' in registro
    assert 'fecha_hora' in registro