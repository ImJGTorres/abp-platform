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
def parametro_base(db):
    """Crea parámetros de prueba en la BD antes de cada test"""
    from apps.configuracion.models import ParametroSistema
    ParametroSistema.objects.create(
        clave="nombre_institucion",
        valor="Universidad Default",
        tipo_dato="string",
        categoria="institucional",
        descripcion="Nombre de la institución"
    )
    ParametroSistema.objects.create(
        clave="max_estudiantes_equipo",
        valor="5",
        tipo_dato="integer",
        categoria="general",
        descripcion="Máximo de estudiantes por equipo"
    )

# -------------------------------------------------------
# CP-01: Ver lista de parámetros como admin → 200
# -------------------------------------------------------
@pytest.mark.django_db
def test_obtener_parametros_como_admin(admin_autenticado, parametro_base):
    url = reverse("configuracion")
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK
    assert len(respuesta.data) > 0

# -------------------------------------------------------
# CP-02: PATCH con valor válido → 200
# -------------------------------------------------------
@pytest.mark.django_db
def test_editar_parametro_valor_valido(admin_autenticado, parametro_base):
    """Verifica que se puede editar un parámetro con valor válido"""
    url = reverse("configuracion_clave", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["valor"] == "UFPS"

# -------------------------------------------------------
# CP-03: PATCH con tipo incorrecto → 400
# -------------------------------------------------------
@pytest.mark.django_db
def test_editar_parametro_tipo_incorrecto(admin_autenticado, parametro_base):
    """Verifica que se rechaza un valor de tipo incorrecto para parámetro integer"""
    url = reverse("configuracion_clave", kwargs={"clave": "max_estudiantes_equipo"})
    datos = {"valor": "abc"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST

# -------------------------------------------------------
# CP-04: Sin autenticación → 401 (unauthorized)
# -------------------------------------------------------
@pytest.mark.django_db
def test_obtener_parametros_sin_autenticacion(cliente, parametro_base):
    url = reverse("configuracion")
    respuesta = cliente.get(url)
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED

# -------------------------------------------------------
# CP-05: Rol no-admin → 403
# -------------------------------------------------------
@pytest.mark.django_db
def test_obtener_parametros_como_estudiante(estudiante_autenticado, parametro_base):
    url = reverse("configuracion")
    respuesta = estudiante_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN

# -------------------------------------------------------
# CP-06: Bitácora — Verifica cambio registrado en bitácora
# -------------------------------------------------------
@pytest.mark.django_db
def test_cambio_parametro_registra_en_bitacora(admin_autenticado, parametro_base):
    """Verifica que al editar un parámetro se registra en la bitácora"""
    from apps.bitacora.models import BitacoraSistema
    url = reverse("configuracion_clave", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS Test"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert BitacoraSistema.objects.filter(
        accion=BitacoraSistema.Accion.UPDATE,
        modulo='configuracion'
    ).exists()

# -------------------------------------------------------
# EXTRA — Prueba del modelo directamente (sin endpoints)
# Esto SÍ puede correr hoy porque el modelo ya existe ✅
# -------------------------------------------------------
@pytest.mark.django_db
def test_modelo_valida_tipo_incorrecto():
    """Verifica que el modelo rechaza valor de tipo incorrecto"""
    from apps.configuracion.models import ParametroSistema
    from django.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        ParametroSistema.objects.create(
            clave="test_entero",
            valor="abc",
            tipo_dato="integer",
            categoria="general"
        )

@pytest.mark.django_db
def test_modelo_acepta_valor_correcto():
    """Verifica que el modelo acepta un entero válido"""
    from apps.configuracion.models import ParametroSistema
    p = ParametroSistema.objects.create(
        clave="test_entero_valido",
        valor="10",
        tipo_dato="integer",
        categoria="general"
    )
    assert p.get_valor_casteado() == 10