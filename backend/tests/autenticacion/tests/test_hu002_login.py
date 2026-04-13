import pytest
from apps.usuarios.models import Usuario

URL_LOGIN   = "/api/auth/login/"
URL_REFRESH = "/api/auth/refresh/"
URL_LOGOUT  = "/api/auth/logout/"

# CP-01: Login con credenciales válidas → 200 + tokens


@pytest.mark.django_db
def test_cp01_login_credenciales_validas(api_client, usuario_activo):
    payload = {
        "correo":     "prueba@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }

    response = api_client.post(URL_LOGIN, payload, format="json")

    assert response.status_code == 200
    data = response.json()
    assert "access"    in data
    assert "refresh"   in data


# CP-02: Login con contraseña incorrecta → 401


@pytest.mark.django_db
def test_cp02_login_contrasena_incorrecta(api_client, usuario_activo):
    payload = {
        "correo":     "prueba@ufps.edu.co",
        "contrasena": "ContrasenaMal123!",
    }

    response = api_client.post(URL_LOGIN, payload, format="json")

    assert response.status_code == 401


# CP-03: Login con correo inexistente → 401


@pytest.mark.django_db
def test_cp03_login_correo_inexistente(api_client):
    payload = {
        "correo":     "noexiste@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }

    response = api_client.post(URL_LOGIN, payload, format="json")

    assert response.status_code == 401
    # El mensaje no debe revelar si el correo existe o no
    data = response.json()
    assert "correo" not in str(data).lower() or "no existe" not in str(data).lower()


# CP-04: Login con usuario inactivo → 403


@pytest.mark.django_db
def test_cp04_login_usuario_inactivo(api_client, usuario_inactivo):
    payload = {
        "correo":     "inactivo@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }

    response = api_client.post(URL_LOGIN, payload, format="json")

    assert response.status_code == 403


# CP-05: Refresh token válido renueva el access token → 200


@pytest.mark.django_db
def test_cp05_refresh_token_valido(api_client, usuario_activo):
    # Primero hacemos login para obtener el refresh token
    login_response = api_client.post(URL_LOGIN, {
        "correo":     "prueba@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }, format="json")

    assert login_response.status_code == 200, "Login previo falló, CP-05 no puede ejecutarse"

    refresh_token = login_response.json()["refresh"]

    # Ahora usamos el refresh token
    response = api_client.post(URL_REFRESH, {"refresh": refresh_token}, format="json")

    assert response.status_code == 200
    assert "access" in response.json()


# CP-06: Logout invalida el refresh token → 200, luego 401


@pytest.mark.django_db
def test_cp06_logout_invalida_refresh_token(api_client, usuario_activo):
    # Login para obtener tokens
    login_response = api_client.post(URL_LOGIN, {
        "correo":     "prueba@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }, format="json")

    assert login_response.status_code == 200, "Login previo falló, CP-06 no puede ejecutarse"

    refresh_token = login_response.json()["refresh"]

    # Logout
    logout_response = api_client.post(URL_LOGOUT, {"refresh": refresh_token}, format="json")
    assert logout_response.status_code == 200

    # Intentar usar el refresh token después del logout → debe fallar
    response = api_client.post(URL_REFRESH, {"refresh": refresh_token}, format="json")
    assert response.status_code == 401


# CP-07: Login exitoso queda registrado en bitácora
# BLOQUEADO hasta que HU-037 ST-03 y ST-04 estén completos


@pytest.mark.skip(reason="Bloqueado: depende de HU-037 ST-03 y ST-04")
@pytest.mark.django_db
def test_cp07_login_registrado_en_bitacora(api_client, usuario_activo):
    from apps.bitacora.models import BitacoraSistema

    api_client.post(URL_LOGIN, {
        "correo":     "prueba@ufps.edu.co",
        "contrasena": "Abcde123!!",
    }, format="json")

    registro = BitacoraSistema.objects.filter(
        id_usuario=usuario_activo.id,
        accion="LOGIN",
        modulo="auth",
    ).last()

    assert registro is not None
    assert registro.fecha_hora is not None