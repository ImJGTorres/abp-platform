import pytest
from apps.roles.models import Rol, Permiso, RolPermiso
from tests.factories import RolFactory, PermisoFactory


@pytest.mark.django_db
def test_cp01_crear_rol_nombre_unico(admin_client):
    data = {
        "nombre": "Administrador General",
        "descripcion": "Rol con todos los permisos"
    }

    response = admin_client.post("/api/roles/", data, format="json")

    assert response.status_code == 201
    assert Rol.objects.filter(nombre="Administrador General").exists()


@pytest.mark.django_db
def test_cp02_crear_rol_nombre_duplicado(admin_client):
    RolFactory(nombre="Duplicado")

    data = {
        "nombre": "Duplicado",
        "descripcion": "Intento duplicado"
    }

    response = admin_client.post("/api/roles/", data, format="json")

    assert response.status_code == 400
    assert "nombre" in response.data


@pytest.mark.django_db
def test_cp03_editar_rol_reemplazar_permisos(admin_client):
    rol = RolFactory()
    permisos = PermisoFactory.create_batch(3)

    data = {
        "nombre": rol.nombre,
        "descripcion": rol.descripcion,
        "permisos": [p.id for p in permisos]
    }

    response = admin_client.put(f"/api/roles/{rol.id}/", data, format="json")

    assert response.status_code == 200

    permisos_ids = RolPermiso.objects.filter(rol=rol).values_list("permiso_id", flat=True)
    assert set(permisos_ids) == set([p.id for p in permisos])


@pytest.mark.django_db
def test_cp04_eliminar_rol_sin_usuarios(admin_client):
    rol = RolFactory()

    response = admin_client.delete(f"/api/roles/{rol.id}/")

    assert response.status_code == 204
    assert not Rol.objects.filter(id=rol.id).exists()


@pytest.mark.django_db
def test_cp05_eliminar_rol_con_usuarios_activos(admin_client, django_user_model):
    rol = RolFactory()

    usuario = django_user_model.objects.create(
        rol=rol,
        tipo_rol="administrador",
        estado="activo",
        contrasena_hash="password123"
    )

    response = admin_client.delete(f"/api/roles/{rol.id}/")

    assert response.status_code == 409
    assert "usuarios" in str(response.data).lower()


@pytest.mark.django_db
def test_cp06_listar_roles_sin_token_y_con_estudiante(api_client, estudiante_client):
    response_sin_token = api_client.get("/api/roles/")
    assert response_sin_token.status_code == 401

    response_estudiante = estudiante_client.get("/api/roles/")
    assert response_estudiante.status_code == 403


@pytest.mark.skip(reason="Bloqueado: depende de HU-037 ST-03 y ST-04")
@pytest.mark.django_db
def test_cp07_bitacora_creacion_rol(admin_client):
    data = {
        "nombre": "Rol Auditor",
        "descripcion": "Para auditoría"
    }

    response = admin_client.post("/api/roles/", data, format="json")

    assert response.status_code == 201