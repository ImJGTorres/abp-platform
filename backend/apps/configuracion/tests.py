from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.hashers import make_password

from apps.usuarios.models import Usuario
from apps.configuracion.models import ParametroSistema


class ParametroSistemaPatchTestCase(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombre='Admin',
            apellido='Test',
            correo='admin@test.com',
            contrasena_hash=make_password('test123'),
            tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
        )
        self.parametro = ParametroSistema.objects.create(
            clave='max_estudiantes_por_equipo',
            valor='5',
            descripcion='Maximo de estudiantes',
            categoria=ParametroSistema.Categoria.GENERAL,
            tipo_dato=ParametroSistema.TipoDato.INTEGER,
        )
        self.client = APIClient()
        
    def _autenticar(self):
        self.client.login(username='admin@test.com', password='test123')
        
    def test_patch_actualizacion_exitosa(self):
        self._autenticar()
        response = self.client.patch(
            '/api/configuracion/max_estudiantes_por_equipo/',
            {'valor': '8'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['valor'], '8')

    def test_patch_parametro_inexistente(self):
        self._autenticar()
        response = self.client.patch(
            '/api/configuracion/no_existe/',
            {'valor': '10'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_valor_requerido(self):
        self._autenticar()
        response = self.client.patch(
            '/api/configuracion/max_estudiantes_por_equipo/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_tipo_invalido(self):
        self._autenticar()
        response = self.client.patch(
            '/api/configuracion/max_estudiantes_por_equipo/',
            {'valor': 'no_es_entero'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_rango_invalido(self):
        self._autenticar()
        response = self.client.patch(
            '/api/configuracion/max_estudiantes_por_equipo/',
            {'valor': '15', 'rango': {'min': 1, 'max': 10}},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)