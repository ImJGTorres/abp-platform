from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth import get_user_model

from apps.bitacora.models import BitacoraSistema


Usuario = get_user_model()


class BitacoraReadOnlyTests(APITestCase):
    """Tests para verificar que el endpoint de bitácora es de solo lectura."""
    
    @classmethod
    def setUpTestData(cls):
        # Crea un usuario administrador para las pruebas
        cls.admin_user = Usuario.objects.create_user(
            nombre='Admin',
            apellido='Test',
            correo='admin@test.com',
            contrasena_hash='testpassword123',
            tipo_rol=Usuario.TipoRol.ADMINISTRADOR,
            estado=Usuario.Estado.ACTIVO,
            is_staff=True,
        )
        
        # Crea un registro de bitácora de prueba
        cls.bitacora = BitacoraSistema.objects.create(
            id_usuario=cls.admin_user,
            nombre_usuario='Admin Test',
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='autenticacion',
            descripcion='Test log entry',
            ip_origen='127.0.0.1',
        )
    
    def _authenticate(self):
        """Autentica las pruebas con el usuario administrador."""
        self.client.force_authenticate(user=self.admin_user)
    
    # Tests para el endpoint de lista /api/bitacora/
    
    def test_get_returns_200(self):
        """Verifica que GET retorna 200 OK."""
        self._authenticate()
        response = self.client.get('/api/bitacora/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_put_returns_405(self):
        """Verifica que PUT retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.put('/api/bitacora/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_patch_returns_405(self):
        """Verifica que PATCH retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.patch('/api/bitacora/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_returns_405(self):
        """Verifica que DELETE retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.delete('/api/bitacora/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # Tests para el endpoint de detalle /api/bitacora/<id>/
    
    def test_get_detail_returns_405(self):
        """Verifica que GET en detalle retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.get(f'/api/bitacora/{self.bitacora.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_put_detail_returns_405(self):
        """Verifica que PUT en detalle retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.put(f'/api/bitacora/{self.bitacora.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_patch_detail_returns_405(self):
        """Verifica que PATCH en detalle retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.patch(f'/api/bitacora/{self.bitacora.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_detail_returns_405(self):
        """Verifica que DELETE en detalle retorna 405 Method Not Allowed."""
        self._authenticate()
        response = self.client.delete(f'/api/bitacora/{self.bitacora.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)