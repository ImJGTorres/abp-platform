# backend/tests/bitacora/test_hu037_auditoria.py
#
# HU-037 — Bitácora de auditoría del sistema
# Subtarea: SCRUM-165 — PR 01 Pruebas unitarias del backend
#
# Estado: ENDPOINT IMPLEMENTADO (/api/bitacora/)
# ─────────────────────────────────────────────────────────────────

import pytest
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
    usuario.is_staff = True
    usuario.save()
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def docente_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
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
def estudiante_autenticado(cliente, db):
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
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
# Tests del Modelo - BitácoraSistema
# -------------------------------------------------------
@pytest.mark.django_db
def test_registrar_evento_crea_registro(evento_base):
    """Verifica que registrar_evento() guarda en la BD"""
    from apps.bitacora.models import BitacoraSistema
    assert BitacoraSistema.objects.exists()
    evento = BitacoraSistema.objects.first()
    assert evento.accion == 'ACCESS'
    assert evento.modulo == 'configuracion'


@pytest.mark.django_db
def test_bitacora_rechaza_update(evento_base):
    """Verifica que el modelo rechaza UPDATE (append-only)"""
    from apps.bitacora.models import BitacoraSistema
    evento = BitacoraSistema.objects.first()
    with pytest.raises(TypeError, match=".*no se permite modificar.*"):
        evento.descripcion = "Intento de cambio"
        evento.save()


@pytest.mark.django_db
def test_bitacora_rechaza_delete(evento_base):
    """Verifica que el modelo rechaza DELETE (append-only)"""
    from apps.bitacora.models import BitacoraSistema
    evento = BitacoraSistema.objects.first()
    with pytest.raises(TypeError, match=".*no se permite DELETE.*"):
        evento.delete()


# -------------------------------------------------------
# Tests de API - Endpoint /api/bitacora/
# -------------------------------------------------------
@pytest.mark.django_db
def test_listar_eventos_como_admin(admin_autenticado, evento_base):
    """GET /api/bitacora/ retorna lista de eventos"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    assert 'results' in respuesta.data or len(respuesta.data) >= 1


@pytest.mark.django_db
def test_listar_eventos_como_docente(docente_autenticado):
    """GET /api/bitacora/ como docente retorna 403"""
    respuesta = docente_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_listar_eventos_como_estudiante(estudiante_autenticado):
    """GET /api/bitacora/ como estudiante retorna 403"""
    respuesta = estudiante_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_listar_eventos_sin_autenticacion(cliente):
    """GET /api/bitacora/ sin autenticacion retorna 401"""
    respuesta = cliente.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_filtrar_eventos_por_modulo(admin_autenticado, evento_base):
    """Filtrar eventos por modulo"""
    respuesta = admin_autenticado.get("/api/bitacora/?modulo=configuracion")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_filtrar_eventos_por_accion(admin_autenticado, evento_base):
    """Filtrar eventos por accion"""
    respuesta = admin_autenticado.get("/api/bitacora/?accion=ACCESS")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_filtrar_eventos_por_fecha_desde(admin_autenticado, evento_base):
    """Filtrar eventos por fecha desde"""
    respuesta = admin_autenticado.get("/api/bitacora/?fecha_desde=2026-01-01")
    assert respuesta.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_registro_contiene_campos_minimos(admin_autenticado, evento_base):
    """Cada registro contiene campos mínimos requeridos"""
    respuesta = admin_autenticado.get("/api/bitacora/")
    assert respuesta.status_code == status.HTTP_200_OK
    data = respuesta.data.get('results', respuesta.data)
    registro = data[0]
    assert 'nombre_usuario' in registro
    assert 'accion' in registro
    assert 'modulo' in registro
    assert 'fecha_hora' in registro