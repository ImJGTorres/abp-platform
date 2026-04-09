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
def admin_autenticado(cliente, django_user_model):
    usuario = django_user_model.objects.create_superuser(
        username="admin_test",
        password="admin123",
        email="admin@test.com"
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def estudiante_autenticado(django_user_model):
    cliente = APIClient()
    usuario = django_user_model.objects.create_user(
        username="estudiante_test",
        password="est123",
        email="estudiante@test.com"
    )
    cliente.force_authenticate(user=usuario)
    return cliente

@pytest.fixture
def parametro_base(db):
    """Crea parámetros de prueba en la BD antes de cada test"""
    from apps.configuracion.models import ParametroSistema  # ✅ nombre correcto
    ParametroSistema.objects.create(
        clave="nombre_institucion",
        valor="Universidad Default",
        tipo_dato="string",
        categoria="institucional",   # ✅ campo obligatorio
        descripcion="Nombre de la institución"
    )
    ParametroSistema.objects.create(
        clave="max_estudiantes_equipo",
        valor="5",
        tipo_dato="integer",
        categoria="general",         # ✅ campo obligatorio
        descripcion="Máximo de estudiantes por equipo"
    )

# -------------------------------------------------------
# CP-01: Ver lista de parámetros como admin → 200
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó views.py")
@pytest.mark.django_db
def test_obtener_parametros_como_admin(admin_autenticado, parametro_base):
    url = reverse("configuracion-list")
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK
    assert len(respuesta.data) > 0

# -------------------------------------------------------
# CP-02: PATCH con valor válido → 200
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó views.py")
@pytest.mark.django_db
def test_editar_parametro_valor_valido(admin_autenticado, parametro_base):
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["valor"] == "UFPS"

# -------------------------------------------------------
# CP-03: PATCH con tipo incorrecto → 400
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó views.py")
@pytest.mark.django_db
def test_editar_parametro_tipo_incorrecto(admin_autenticado, parametro_base):
    url = reverse("configuracion-detail", kwargs={"clave": "max_estudiantes_equipo"})
    datos = {"valor": "abc"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST

# -------------------------------------------------------
# CP-04: Sin autenticación → 401
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó views.py")
@pytest.mark.django_db
def test_obtener_parametros_sin_autenticacion(cliente, parametro_base):
    url = reverse("configuracion-list")
    respuesta = cliente.get(url)
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED

# -------------------------------------------------------
# CP-05: Rol no-admin → 403
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: Gabriel aún no implementó views.py")
@pytest.mark.django_db
def test_editar_parametro_como_estudiante(estudiante_autenticado, parametro_base):
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "Intento no autorizado"}
    respuesta = estudiante_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_403_FORBIDDEN

# -------------------------------------------------------
# CP-06: Bitácora — BLOQUEADO hasta HU-037
# -------------------------------------------------------
@pytest.mark.skip(reason="Bloqueado: depende de HU-037 ST-03 y ST-04")
@pytest.mark.django_db
def test_cambio_parametro_registra_en_bitacora(admin_autenticado, parametro_base):
    from apps.bitacora.models import BitacoraEvento
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS Test"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert BitacoraEvento.objects.exists()

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
            valor="abc",           # tipo incorrecto para integer
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