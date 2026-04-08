import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


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


# -------------------------------------------------------
# CASO 1: Ver lista de parámetros de configuración
# -------------------------------------------------------
@pytest.mark.django_db
def test_obtener_parametros_como_admin(admin_autenticado):
    url = reverse("configuracion-list")
    respuesta = admin_autenticado.get(url)
    assert respuesta.status_code == status.HTTP_200_OK


# -------------------------------------------------------
# CASO 2: Editar un parámetro con valor válido
# -------------------------------------------------------
@pytest.mark.django_db
def test_editar_parametro_valor_valido(admin_autenticado):
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS"}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_200_OK
    assert respuesta.data["valor"] == "UFPS"


# -------------------------------------------------------
# CASO 3: Editar un parámetro con valor vacío
# -------------------------------------------------------
@pytest.mark.django_db
def test_editar_parametro_valor_vacio(admin_autenticado):
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": ""}
    respuesta = admin_autenticado.patch(url, datos, format="json")
    assert respuesta.status_code == status.HTTP_400_BAD_REQUEST


# -------------------------------------------------------
# CASO 4: Usuario no autenticado no puede ver parámetros
# -------------------------------------------------------
@pytest.mark.django_db
def test_obtener_parametros_sin_autenticacion(cliente):
    url = reverse("configuracion-list")
    respuesta = cliente.get(url)
    assert respuesta.status_code == status.HTTP_401_UNAUTHORIZED


# -------------------------------------------------------
# CASO 5: Verificar que el cambio queda registrado en bitácora
# -------------------------------------------------------
@pytest.mark.django_db
def test_cambio_parametro_registra_en_bitacora(admin_autenticado):
    from apps.bitacora.models import BitacoraEvento
    url = reverse("configuracion-detail", kwargs={"clave": "nombre_institucion"})
    datos = {"valor": "UFPS Test"}
    admin_autenticado.patch(url, datos, format="json")
    assert BitacoraEvento.objects.filter(accion__icontains="configuracion").exists()