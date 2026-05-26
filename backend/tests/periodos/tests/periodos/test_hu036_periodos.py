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
#
# NOTA DE ARQUITECTURA:
# Los fixtures `api_client`, `admin_client` y `estudiante_autenticado` están
# definidos en tests/conftest.py y son compartidos por todos los módulos de
# prueba. NO deben redefinirse localmente para evitar duplicación.
# ─────────────────────────────────────────────────────────────────

import pytest
from rest_framework import status
from apps.configuracion.models import PeriodoAcademico
from tests.factories import AdminFactory

# -------------------------------------------------------
# Fixtures locales (solo los que son específicos de este módulo)
# -------------------------------------------------------

@pytest.fixture
def periodo_base(db):
    """Crea dos períodos académicos de prueba: uno activo y uno inactivo.

    Utiliza AdminFactory para evitar duplicar la lógica de creación de
    usuarios que ya está centralizada en tests/factories.py.
    """
    usuario = AdminFactory()
    PeriodoAcademico.objects.create(
        nombre="2026-1",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo",
        usuario_creo=usuario,
    )
    PeriodoAcademico.objects.create(
        nombre="2025-2",
        fecha_inicio="2025-08-01",
        fecha_fin="2025-12-15",
        estado="inactivo",
        usuario_creo=usuario,
    )


# -------------------------------------------------------
# Tests de API - Periodos Académicos
# -------------------------------------------------------

@pytest.mark.django_db
def test_crear_periodo_exitoso(admin_client):
    """Un administrador puede crear un período con fechas coherentes."""
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo",
    }
    respuesta = admin_client.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_201_CREATED
    assert respuesta.data["nombre"] == "2026-2"


@pytest.mark.django_db
def test_crear_periodo_fechas_incoherentes(admin_client):
    """Crear un período con fecha_fin anterior a fecha_inicio devuelve 400."""
    datos = {
        "nombre": "2026-error",
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-01-01",
        "estado": "activo",
    }
    respuesta = admin_client.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_actualizar_periodo(admin_client, periodo_base):
    """Un administrador puede actualizar la fecha_fin de un período existente."""
    periodo = PeriodoAcademico.objects.get(nombre="2026-1")
    datos = {
        "nombre": "2026-1",
        "fecha_inicio": "2026-02-01",
        "fecha_fin": "2026-07-15",
        "estado": "activo",
    }
    respuesta = admin_client.put(f"/api/periodos/{periodo.id}/", datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["fecha_fin"] == "2026-07-15"


@pytest.mark.django_db
def test_eliminar_periodo_sin_cursos(admin_client, periodo_base):
    """Un administrador puede eliminar un período que no tiene cursos asociados."""
    periodo = PeriodoAcademico.objects.get(nombre="2025-2")
    respuesta = admin_client.delete(f"/api/periodos/{periodo.id}/")
    assert respuesta.status_code == status.HTTP_204_NO_CONTENT
    assert not PeriodoAcademico.objects.filter(nombre="2025-2").exists()


@pytest.mark.django_db
def test_solo_un_periodo_activo(admin_client, periodo_base):
    """Al crear un nuevo período activo, el anterior debe quedar inactivo."""
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo",
    }
    admin_client.post("/api/periodos/", datos, format="json")
    activos = PeriodoAcademico.objects.filter(estado="activo")
    assert activos.count() == 1
    assert activos.first().nombre == "2026-2"


@pytest.mark.django_db
def test_listar_periodos_sin_autenticacion(api_client):
    """Un cliente sin autenticar recibe 401 al intentar listar períodos."""
    respuesta = api_client.get("/api/periodos/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


# -------------------------------------------------------
# Tests del Modelo — Validaciones de negocio
# -------------------------------------------------------

@pytest.mark.django_db
def test_modelo_valida_fechas_incoherentes():
    """El modelo rechaza períodos con fecha_fin anterior a fecha_inicio."""
    from django.db import IntegrityError
    usuario = AdminFactory()
    with pytest.raises(IntegrityError):
        PeriodoAcademico.objects.create(
            nombre="2026-test-err",
            fecha_inicio="2026-06-01",
            fecha_fin="2026-01-01",
            estado="activo",
            usuario_creo=usuario,
        )


@pytest.mark.django_db
def test_modelo_acepta_periodo_valido():
    """El modelo acepta y persiste un período con fechas coherentes."""
    usuario = AdminFactory()
    p = PeriodoAcademico.objects.create(
        nombre="2026-test",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo",
        usuario_creo=usuario,
    )
    assert p.id is not None
    assert p.nombre == "2026-test"