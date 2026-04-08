import pytest
from django.contrib.auth.hashers import check_password
from apps.usuarios.models import Usuario
from tests.factories import UsuarioFactory

URL = "/api/usuarios/"

# CP-01: Creación exitosa → 201

@pytest.mark.django_db
def test_cp01_crear_usuario_exitoso(admin_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = admin_client.post(URL, payload, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["correo"]   == "ana@ufps.edu.co"
    assert data["tipo_rol"] == "estudiante"
    assert "contrasena"      not in data
    assert "contrasena_hash" not in data

# CP-02: Correo duplicado → 400

@pytest.mark.django_db
def test_cp02_correo_duplicado(admin_client):
    UsuarioFactory(correo="ana@ufps.edu.co")  # ya existe en BD

    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = admin_client.post(URL, payload, format="json")

    assert response.status_code == 400
    assert "correo" in response.json()

# CP-03: Campo obligatorio faltante → 400

@pytest.mark.django_db
def test_cp03_campo_correo_faltante(admin_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        # correo omitido intencionalmente
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = admin_client.post(URL, payload, format="json")

    assert response.status_code == 400
    assert "correo" in response.json()

# CP-04: Rol inválido → 400

@pytest.mark.django_db
def test_cp04_rol_invalido(admin_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana2@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "superusuario",  # no existe en TipoRol
    }

    response = admin_client.post(URL, payload, format="json")

    assert response.status_code == 400
    assert "tipo_rol" in response.json()

# CP-05: Contraseña almacenada cifrada en BD

@pytest.mark.django_db
def test_cp05_contrasena_almacenada_cifrada(admin_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana3@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = admin_client.post(URL, payload, format="json")
    assert response.status_code == 201

    usuario = Usuario.objects.get(correo="ana3@ufps.edu.co")

    # No debe guardarse en texto plano
    assert usuario.contrasena_hash != "Abcde123!"
    # Debe verificarse correctamente con el hasher de Django
    assert check_password("Abcde123!", usuario.contrasena_hash)

# CP-06: Sin autenticación → 401

@pytest.mark.django_db
def test_cp06_sin_token_retorna_401(api_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana4@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = api_client.post(URL, payload, format="json")

    assert response.status_code == 401

# CP-07: Rol no-admin → 403

@pytest.mark.django_db
def test_cp07_estudiante_no_puede_crear_usuario(estudiante_client):
    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana5@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = estudiante_client.post(URL, payload, format="json")

    assert response.status_code == 403

# CP-08: Registro en bitácora
# BLOQUEADO hasta que HU-037 ST-03 y ST-04 estén completos

@pytest.mark.skip(reason="Bloqueado: depende de HU-037 ST-03 y ST-04")
@pytest.mark.django_db
def test_cp08_creacion_registrada_en_bitacora(admin_client, admin_user):
    from apps.bitacora.models import BitacoraSistema  # se importa aquí para no romper si el módulo no existe aún

    payload = {
        "nombre":    "Ana",
        "apellido":  "López",
        "correo":    "ana6@ufps.edu.co",
        "contrasena": "Abcde123!",
        "tipo_rol":  "estudiante",
    }

    response = admin_client.post(URL, payload, format="json")
    assert response.status_code == 201

    usuario_creado_id = response.json()["id"]

    registro = BitacoraSistema.objects.filter(
        id_usuario=admin_user.id,
        accion="CREATE",
        modulo="usuarios",
    ).last()

    assert registro is not None
    assert str(usuario_creado_id) in registro.descripcion
    assert registro.fecha_hora is not None