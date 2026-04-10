# backend/tests/periodos/test_hu036_periodos.py
#
# HU-036 — Como administrador, quiero gestionar periodos académicos.
# Subtarea: SCRUM-164 — PR 01 Pruebas unitarias del backend
#
# GUÍA PARA GABRIEL (backend):
# ─────────────────────────────────────────────────────────────────
# Modelo esperado:   apps.periodos.models.PeriodoAcademico
# Campos requeridos: nombre, fecha_inicio, fecha_fin, estado, (FK cursos)
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
def admin_autenticado(cliente, django_user_model):
    from apps.usuarios.models import Usuario
    usuario = Usuario.objects.create_superuser(
        username="admin_test",
        password="admin123",
        email="admin@test.com"
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def estudiante_autenticado(django_user_model):
    from apps.usuarios.models import Usuario
    cliente = APIClient()
    usuario = Usuario.objects.create_user(
        username="estudiante_test",
        password="est123",
        email="estudiante@test.com"
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def periodo_base(db):
    """
    Crea periodos de prueba en la BD.
    GABRIEL: el modelo debe llamarse PeriodoAcademico con estos campos:
      - nombre: CharField único (ej. "2026-1")
      - fecha_inicio: DateField
      - fecha_fin: DateField  (debe ser > fecha_inicio)
      - estado: CharField con opciones activo/inactivo/cerrado
    """
    from apps.periodos.models import PeriodoAcademico  # ⚠️ ajustar según Gabriel
    PeriodoAcademico.objects.create(
        nombre="2026-1",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo"
    )
    PeriodoAcademico.objects.create(
        nombre="2025-2",
        fecha_inicio="2025-08-01",
        fecha_fin="2025-12-15",
        estado="inactivo"
    )

# -------------------------------------------------------
# CP-01: POST crea periodo correctamente → 201
# GABRIEL: endpoint POST /api/periodos/ requerido
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó POST /api/periodos/")
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

# -------------------------------------------------------
# CP-02: POST con fechas incoherentes → 400
# GABRIEL: validar que fecha_fin > fecha_inicio en el serializer
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó POST /api/periodos/")
@pytest.mark.django_db
def test_crear_periodo_fechas_incoherentes(admin_autenticado):
    datos = {
        "nombre": "2026-error",
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-01-01",  # fin ANTES que inicio
        "estado": "activo"
    }
    respuesta = admin_autenticado.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST

# -------------------------------------------------------
# CP-03: PUT actualiza periodo existente → 200
# GABRIEL: endpoint PUT /api/periodos/:id/ requerido
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó PUT /api/periodos/:id/")
@pytest.mark.django_db
def test_actualizar_periodo(admin_autenticado, periodo_base):
    from apps.periodos.models import PeriodoAcademico
    periodo = PeriodoAcademico.objects.get(nombre="2026-1")
    datos = {
        "nombre": "2026-1",
        "fecha_inicio": "2026-02-01",
        "fecha_fin": "2026-07-15",  # nueva fecha fin
        "estado": "activo"
    }
    respuesta = admin_autenticado.put(
        f"/api/periodos/{periodo.id}/", datos, format="json"
    )
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["fecha_fin"] == "2026-07-15"

# -------------------------------------------------------
# CP-04: DELETE periodo sin cursos → 204
# GABRIEL: endpoint DELETE /api/periodos/:id/ requerido
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó DELETE /api/periodos/:id/")
@pytest.mark.django_db
def test_eliminar_periodo_sin_cursos(admin_autenticado, periodo_base):
    from apps.periodos.models import PeriodoAcademico
    periodo = PeriodoAcademico.objects.get(nombre="2025-2")
    respuesta = admin_autenticado.delete(f"/api/periodos/{periodo.id}/")
    assert respuesta.status_code == status.HTTP_204_NO_CONTENT
    assert not PeriodoAcademico.objects.filter(nombre="2025-2").exists()

# -------------------------------------------------------
# CP-05: DELETE periodo con cursos asociados → 409
# GABRIEL: si el periodo tiene cursos asociados (FK), no permitir eliminar
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó DELETE + validación FK cursos")
@pytest.mark.django_db
def test_eliminar_periodo_con_cursos(admin_autenticado, periodo_base):
    from apps.periodos.models import PeriodoAcademico
    # TODO: asociar curso al periodo cuando exista el modelo Curso
    periodo = PeriodoAcademico.objects.get(nombre="2026-1")
    respuesta = admin_autenticado.delete(f"/api/periodos/{periodo.id}/")
    assert respuesta.status_code == status.HTTP_409_CONFLICT

# -------------------------------------------------------
# CP-06: Solo un periodo activo a la vez
# GABRIEL: al activar un periodo, los demás deben pasar a "inactivo"
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó regla de negocio de estado")
@pytest.mark.django_db
def test_solo_un_periodo_activo(admin_autenticado, periodo_base):
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo"
    }
    admin_autenticado.post("/api/periodos/", datos, format="json")
    from apps.periodos.models import PeriodoAcademico
    activos = PeriodoAcademico.objects.filter(estado="activo")
    assert activos.count() == 1
    assert activos.first().nombre == "2026-2"

# -------------------------------------------------------
# CP-07: Sin autenticación → 401
# GABRIEL: proteger todos los endpoints con autenticación JWT
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó GET /api/periodos/")
@pytest.mark.django_db
def test_listar_periodos_sin_autenticacion(cliente):
    respuesta = cliente.get("/api/periodos/")
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED

# -------------------------------------------------------
# CP-08: Rol no-admin → 403
# GABRIEL: solo administradores pueden gestionar periodos
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó permisos por rol")
@pytest.mark.django_db
def test_estudiante_no_puede_crear_periodo(estudiante_autenticado):
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo"
    }
    respuesta = estudiante_autenticado.post("/api/periodos/", datos, format="json")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN

# -------------------------------------------------------
# CP-09: Operaciones registradas en bitácora
# GABRIEL: llamar BitacoraSistema al hacer CREATE, UPDATE, DELETE
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: depende de endpoints + HU-037 BitacoraSistema")
@pytest.mark.django_db
def test_operaciones_registradas_en_bitacora(admin_autenticado, periodo_base):
    from apps.bitacora.models import BitacoraSistema
    datos = {
        "nombre": "2026-2",
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-12-15",
        "estado": "activo"
    }
    admin_autenticado.post("/api/periodos/", datos, format="json")
    assert BitacoraSistema.objects.filter(
        accion="CREATE",
        modulo="periodos"
    ).exists()

# -------------------------------------------------------
# TESTS DEL MODELO — corren HOY sin esperar a Gabriel
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: apps.periodos no existe aún")
@pytest.mark.django_db
def test_modelo_valida_fechas_incoherentes():
    """El modelo debe rechazar fecha_fin <= fecha_inicio"""
    from apps.periodos.models import PeriodoAcademico
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        PeriodoAcademico.objects.create(
            nombre="test-error",
            fecha_inicio="2026-06-01",
            fecha_fin="2026-01-01",
            estado="activo"
        )

@pytest.mark.skip(reason="Bloqueado: apps.periodos no existe aún")
@pytest.mark.django_db
def test_modelo_acepta_periodo_valido():
    """El modelo acepta un periodo con fechas coherentes"""
    from apps.periodos.models import PeriodoAcademico
    p = PeriodoAcademico.objects.create(
        nombre="2026-test",
        fecha_inicio="2026-02-01",
        fecha_fin="2026-06-30",
        estado="activo"
    )
    assert p.id is not None
    assert p.nombre == "2026-test"