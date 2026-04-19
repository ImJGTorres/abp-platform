from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioUpdateSerializer


def crear_usuario(correo, rol=Usuario.TipoRol.ESTUDIANTE, estado=Usuario.Estado.ACTIVO, **kwargs):
    u = Usuario(correo=correo, tipo_rol=rol, estado=estado, **kwargs)
    u.set_password('password123')
    u.save()
    return u


class LoginViewTests(APITestCase):
    URL = '/api/auth/login/'

    def setUp(self):
        self.usuario = crear_usuario('ana@test.com', nombre='Ana', apellido='García')
        self.usuario_inactivo = crear_usuario(
            'bob@test.com', nombre='Bob', apellido='López',
            estado=Usuario.Estado.INACTIVO,
        )

    def test_login_exitoso_retorna_tokens(self):
        resp = self.client.post(self.URL, {'correo': 'ana@test.com', 'contrasena': 'password123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_contrasena_incorrecta_retorna_401(self):
        resp = self.client.post(self.URL, {'correo': 'ana@test.com', 'contrasena': 'wrong'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_correo_inexistente_retorna_401(self):
        resp = self.client.post(self.URL, {'correo': 'noexiste@test.com', 'contrasena': 'password123'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_usuario_inactivo_retorna_401(self):
        resp = self.client.post(self.URL, {'correo': 'bob@test.com', 'contrasena': 'password123'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_sin_campos_retorna_400(self):
        resp = self.client.post(self.URL, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# BD-01: Verificar campos editables en la tabla de usuarios
class UsuarioUpdateSerializerTests(TestCase):

    def setUp(self):
        self.usuario = crear_usuario(
            'juan@test.com', nombre='Juan', apellido='Pérez',
            rol=Usuario.TipoRol.DOCENTE,
        )
        self.admin = crear_usuario(
            'admin@test.com', nombre='Admin', apellido='Root',
            rol=Usuario.TipoRol.ADMINISTRADOR,
        )

    def _serializer(self, instance, data, request_user):
        from unittest.mock import Mock
        request = Mock()
        request.user = request_user
        return UsuarioUpdateSerializer(instance, data=data, partial=True, context={'request': request})

    # --- Campos libres para cualquier usuario autenticado ---

    def test_nombre_es_editable(self):
        s = self._serializer(self.usuario, {'nombre': 'Carlos'}, self.usuario)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre, 'Carlos')

    def test_apellido_es_editable(self):
        s = self._serializer(self.usuario, {'apellido': 'Ramírez'}, self.usuario)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.apellido, 'Ramírez')

    def test_telefono_es_editable(self):
        s = self._serializer(self.usuario, {'telefono': '3001234567'}, self.usuario)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.telefono, '3001234567')

    def test_foto_perfil_es_editable(self):
        url = 'https://cdn.example.com/foto.jpg'
        s = self._serializer(self.usuario, {'foto_perfil': url}, self.usuario)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.foto_perfil, url)

    # --- Restricciones para correo y rol ---

    def test_correo_no_editable_sin_admin(self):
        s = self._serializer(self.usuario, {'correo': 'nuevo@test.com'}, self.usuario)
        self.assertFalse(s.is_valid())
        self.assertIn('correo', s.errors)

    def test_rol_no_editable_sin_admin(self):
        s = self._serializer(self.usuario, {'tipo_rol': Usuario.TipoRol.ADMINISTRADOR}, self.usuario)
        self.assertFalse(s.is_valid())
        self.assertIn('tipo_rol', s.errors)

    def test_correo_editable_por_admin(self):
        s = self._serializer(self.usuario, {'correo': 'nuevo@test.com'}, self.admin)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.correo, 'nuevo@test.com')

    def test_rol_editable_por_admin(self):
        s = self._serializer(self.usuario, {'tipo_rol': Usuario.TipoRol.LIDER_EQUIPO}, self.admin)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.tipo_rol, Usuario.TipoRol.LIDER_EQUIPO)

    def test_correo_duplicado_retorna_error(self):
        s = self._serializer(self.usuario, {'correo': 'admin@test.com'}, self.admin)
        self.assertFalse(s.is_valid())
        self.assertIn('correo', s.errors)

    def test_nombre_minimo_2_caracteres(self):
        s = self._serializer(self.usuario, {'nombre': 'X'}, self.usuario)
        self.assertFalse(s.is_valid())
        self.assertIn('nombre', s.errors)

    def test_apellido_minimo_2_caracteres(self):
        s = self._serializer(self.usuario, {'apellido': 'Z'}, self.usuario)
        self.assertFalse(s.is_valid())
        self.assertIn('apellido', s.errors)


class UsuarioProfileViewTests(APITestCase):
    URL = '/api/usuarios/perfil/'

    def setUp(self):
        self.usuario = crear_usuario('maria@test.com', nombre='María', apellido='López')
        self.admin = crear_usuario(
            'admin2@test.com', nombre='Admin', apellido='Root',
            rol=Usuario.TipoRol.ADMINISTRADOR,
        )

    def _auth(self, user):
        refresh = RefreshToken()
        refresh['user_id'] = user.id
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    def test_patch_campos_libres_retorna_200(self):
        self._auth(self.usuario)
        resp = self.client.patch(self.URL, {'nombre': 'Mariana', 'telefono': '3119876543'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Mariana')

    def test_patch_correo_sin_admin_retorna_400(self):
        self._auth(self.usuario)
        resp = self.client.patch(self.URL, {'correo': 'hack@test.com'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('correo', resp.data)

    def test_patch_rol_sin_admin_retorna_400(self):
        self._auth(self.usuario)
        resp = self.client.patch(self.URL, {'tipo_rol': Usuario.TipoRol.ADMINISTRADOR})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tipo_rol', resp.data)

    def test_patch_sin_autenticacion_retorna_401(self):
        resp = self.client.patch(self.URL, {'nombre': 'Hacker'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)