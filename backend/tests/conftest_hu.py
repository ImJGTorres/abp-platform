"""
Helper functions for HU-029 to HU-034 unit tests.

No es un conftest de pytest (ya existe backend/tests/conftest.py que no se toca).
Importar explícitamente en cada archivo: from conftest_hu import make_payload, authenticated_request, auth_ctx
"""
import json
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from django.test import RequestFactory


def make_user(user_id=1, tipo_rol='director', nombre='Test', correo='test@ufps.edu.co'):
    """Crea un mock de Usuario con los atributos que usan las views (request.user.tipo_rol, etc.)."""
    user = MagicMock()
    user.id = user_id
    user.tipo_rol = tipo_rol
    user.nombre = nombre
    user.apellido = 'Test'
    user.correo = correo
    user.is_authenticated = True
    return user


def make_payload(user_id=1, tipo_rol='director', nombre='Test', correo='test@ufps.edu.co'):
    """Dict de payload; se pasa a authenticated_request para construir el mock de usuario."""
    return {'id': user_id, 'tipo_rol': tipo_rol, 'nombre': nombre, 'correo': correo}


def authenticated_request(factory, method, path, payload, data=None, query_params=None):
    """
    Crea un Django HttpRequest con un mock de usuario en req._mock_user.
    Usar junto con auth_ctx() para inyectar el usuario en la view DRF.
    """
    if method == 'GET':
        req = factory.get(path, data=query_params or {})
    elif method == 'POST':
        req = factory.post(
            path, data=json.dumps(data or {}), content_type='application/json'
        )
    elif method == 'PATCH':
        req = factory.patch(
            path, data=json.dumps(data or {}), content_type='application/json'
        )
    else:
        raise ValueError(f"Método no soportado: {method}")

    req._mock_user = make_user(
        user_id=payload['id'],
        tipo_rol=payload['tipo_rol'],
        nombre=payload.get('nombre', 'Test'),
        correo=payload.get('correo', 'test@ufps.edu.co'),
    )
    return req


@contextmanager
def auth_ctx(req):
    """
    Context manager que parchea UsuarioJWTAuthentication.authenticate para retornar
    req._mock_user, evitando la validación real de JWT en tests unitarios.
    """
    from apps.usuarios.authentication import UsuarioJWTAuthentication
    mock_user = getattr(req, '_mock_user', MagicMock())
    with patch.object(
        UsuarioJWTAuthentication, 'authenticate', return_value=(mock_user, None)
    ):
        yield mock_user
