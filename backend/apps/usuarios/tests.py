from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import Usuario


class LoginViewTests(APITestCase):
    URL = '/api/auth/login/'

    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre='Ana',
            apellido='García',
            correo='ana@test.com',
            contrasena_hash=make_password('password123'),
            tipo_rol=Usuario.TipoRol.ESTUDIANTE,
            estado=Usuario.Estado.ACTIVO,
        )
        self.usuario_inactivo = Usuario.objects.create(
            nombre='Bob',
            apellido='López',
            correo='bob@test.com',
            contrasena_hash=make_password('password123'),
            tipo_rol=Usuario.TipoRol.ESTUDIANTE,
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
