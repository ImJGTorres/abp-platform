from django.contrib.auth.hashers import check_password
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from apps.usuarios.permissions import EsAdministrador
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer, UsuarioUpdateSerializer


class UsuarioProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)

    def patch(self, request):
        usuario = request.user
        serializer = UsuarioUpdateSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UsuarioSerializer(usuario).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# LoginView: View personalizada para autenticación JWT (BE-02, BE-03)
# Maneja el inicio de sesión retornando tokens JWT
# Permite acceso sin token (AllowAny) ya que es el proceso de login
class LoginView(APIView):
    # permission_classes: Permite acceso público para poder hacer login
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Endpoint POST /api/auth/login/
        Proceso de autenticación:
        1. Recibe correo y contraseña en body JSON
        2. Valida credenciales contra modelo Usuario
        3. Retorna access + refresh tokens JWT
        """
        # Extrae credenciales del request JSON
        # .strip() elimina espacios en blanco al inicio/final del correo
        correo    = request.data.get('correo', '').strip()
        contrasena = request.data.get('contrasena', '')

        # Valida que ambos campos existan
        if not correo or not contrasena:
            return Response(
                {'detail': 'correo y contrasena son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Busca usuario en la base de datos por correo
        # Modelo personalizado: apps.usuarios.models.Usuario
        try:
            usuario = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            usuario = None

        # Verifica contraseña usando bcrypt (Django hasher)
        # check_password: función segura que compara hash almacenado
        if usuario is None or not check_password(contrasena, usuario.contrasena_hash):
            # Registra intento fallido en bitácora para auditoría
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.ACCESS_DENIED,
                modulo='autenticacion',
                descripcion=f'Intento de login fallido para correo: {correo}',
            )
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verifica estado del usuario (BE-02)
        # Solo usuarios activos pueden iniciar sesión
        if usuario.estado != Usuario.Estado.ACTIVO:
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.ACCESS_DENIED,
                modulo='autenticacion',
                descripcion=f'Login denegado, usuario inactivo: {correo}',
            )
            return Response(
                {'detail': 'Usuario inactivo.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Genera tokens JWT (BE-03)
        # RefreshToken: Clase de SimpleJWT que crea par access+refresh
        refresh = RefreshToken()
        
        # Personalización del payload del token (BE-03)
        # Agrega datos del usuario al token para evitar llamadas adicionales
        # El frontend puede leer estos datos del access token directamente
        # Campos incluios en el token:
        refresh['user_id']   = usuario.id      # ID único del usuario
        refresh['nombre']   = usuario.nombre # Nombre para mostrar en UI
        refresh['correo']  = usuario.correo  # Correo del usuario
        refresh['tipo_rol'] = usuario.tipo_rol # Rol: admin, docente, estudiante

        # Asigna usuario al request para uso en permisos/logging
        request.usuario = usuario
        # Registra login exitoso en bitácora
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.LOGIN,
            modulo='autenticacion',
            descripcion=f'Login efectivo: {correo}',
        )

        # Retorna tokens al cliente
        # access: Token corto (1 hora) para solicitudes API
        # refresh: Token largo (7 días) para obtener nuevos access
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class UsuarioCreateView(generics.CreateAPIView):
    queryset         = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdministrador]

    def perform_create(self, serializer):
        usuario_creado = serializer.save()      # 1. guarda el usuario en BD
        registrar_evento(                        # 2. registra en bitácora (ST-08)
            request=self.request,               # ← saca la IP y el admin automáticamente
            accion=BitacoraSistema.Accion.CREATE,
            modulo='usuarios',
            descripcion=f'Usuario creado: ID={usuario_creado.id}, correo={usuario_creado.correo}',
        )


class LogoutView(TokenBlacklistView):
    """Vista personalizada para cerrar sesión y registrar el evento en bitácora."""
    def post(self, request, *args, **kwargs):
        user = request.user
        if user and user.is_authenticated:
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.LOGOUT,
                modulo='autenticacion',
                descripcion=f'Logout efectivo: {user.correo}',
            )
        return super().post(request, *args, **kwargs)