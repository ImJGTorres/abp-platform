# backend/tests/periodos/test_hu036_periodos.py
#
# HU-036 — Como administrador, quiero gestionar periodos académicos.
# Subtarea: SCRUM-164 — PR 01 Pruebas unitarias del backend
#
# GUÍA PARA GABRIEL (backend):
# ─────────────────────────────────────────────────────────────────
# Modelo esperado:   apps.configuracion.models.PeriodoAcademico
# Campos requeridos: nombre, fecha_inicio, fecha_fin, estado, usuario_creo
# URL base:          /api/periodos/
# ViewSet:           Router con lookup_field='pk'
# Permisos:          Solo administrador puede crear/editar/eliminar
# Regla de negocio:  Solo un periodo puede estar "activo" a la vez
# Bitácora:          Registrar CREATE, UPDATE, DELETE en BitacoraSistema
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
def periodo_base(db):
    from apps.configuracion.models import PeriodoAcademico
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    
    usuario = Usuario.objects.create(
        nombre="Test",
        apellido="User",
        correo="test@user.com",
        contrasena_hash=make_password("test123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    
    PeriodoAcademico.objects.create(
        nombre="2026-1",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo",
        usuario_creo=usuario
    )
    PeriodoAcademico.objects.create(
        nombre="2025-2",
        fecha_inicio="2025-08-01",
        fecha_fin="2025-12-15",
        estado="inactivo",
        usuario_creo=usuario
    )


# -------------------------------------------------------
# Tests de API - Periodos Académicos
# -------------------------------------------------------
@pytest.mark.django_db
def test_crear_periodo_exitoso(admin_autenticado):
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo"
    }
    respuesta = admin_autenticado.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_201_CREATED
    assert respuesta.data["nombre"] == "2026-2"


@pytest.mark.django_db
def test_crear_periodo_fechas_incoherentes(admin_autenticado):
    datos = {
        "nombre": "2026-error",
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-01-01",
        "estado": "activo"
    }
    respuesta = admin_autenticado.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_actualizar_periodo(admin_autenticado, periodo_base):
    from apps.configuracion.models import PeriodoAcademico
    periodo = PeriodoAcademico.objects.get(nombre="2026-1")
    datos = {
        "nombre": "2026-1",
        "fecha_inicio": "2026-02-01",
        "fecha_fin": "2026-07-15",
        "estado": "activo"
    }
    respuesta = admin_autenticado.put(
        f"/api/periodos/{periodo.id}/", datos, format="json"
    )
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["fecha_fin"] == "2026-07-15"


@pytest.mark.django_db
def test_eliminar_periodo_sin_cursos(admin_autenticado, periodo_base):
    from apps.configuracion.models import PeriodoAcademico
    periodo = PeriodoAcademico.objects.get(nombre="2025-2")
    respuesta = admin_autenticado.delete(f"/api/periodos/{periodo.id}/")
    assert respuesta.status_code == status.HTTP_204_NO_CONTENT
    assert not PeriodoAcademico.objects.filter(nombre="2025-2").exists()


@pytest.mark.django_db
def test_solo_un_periodo_activo(admin_autenticado, periodo_base):
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo"
    }
    admin_autenticado.post("/api/periodos/", datos, format="json")
    from apps.configuracion.models import PeriodoAcademico
    activos = PeriodoAcademico.objects.filter(estado="activo")
    assert activos.count() == 1
    assert activos.first().nombre == "2026-2"


@pytest.mark.django_db
def test_listar_periodos_sin_autenticacion(cliente):
    respuesta = cliente.get("/api/periodos/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


# -------------------------------------------------------
# Tests del Modelo — Validaciones de negocio
# -------------------------------------------------------
@pytest.mark.django_db
def test_modelo_valida_fechas_incoherentes():
    from apps.configuracion.models import PeriodoAcademico
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    from django.db import IntegrityError
    
    usuario = Usuario.objects.create(
        nombre="Test",
        apellido="User",
        correo="test@validation.com",
        contrasena_hash=make_password("test123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    
    with pytest.raises(IntegrityError):
        PeriodoAcademico.objects.create(
            nombre="2026-test-err",
            fecha_inicio="2026-06-01",
            fecha_fin="2026-01-01",
            estado="activo",
            usuario_creo=usuario
        )


@pytest.mark.django_db
def test_modelo_acepta_periodo_valido():
    from apps.configuracion.models import PeriodoAcademico
    from apps.usuarios.models import Usuario
    from django.contrib.auth.hashers import make_password
    
    usuario = Usuario.objects.create(
        nombre="Test",
        apellido="User",
        correo="test@valid.com",
        contrasena_hash=make_password("test123"),
        tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        estado=Usuario.Estado.ACTIVO
    )
    
    p = PeriodoAcademico.objects.create(
        nombre="2026-test",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo",
        usuario_creo=usuario
    )
    assert p.id is not None
    assert p.nombre == "2026-test"