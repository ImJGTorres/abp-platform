import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from decouple import config as env_config

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated

from apps.usuarios.permissions import EsAdministrador
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenBlacklistView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.models import TokenRecuperacion, Usuario
from apps.usuarios.serializers import (
    OlvidarContrasenaSerializer,
    RecuperarContrasenaSerializer,
    UsuarioSerializer,
    UsuarioUpdateSerializer,
)


class UsuarioProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)

    def patch(self, request):
        usuario = request.user
        serializer = UsuarioUpdateSerializer(
            usuario, data=request.data, partial=True, context={'request': request}
        )
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

        # check_password() es el método de AbstractBaseUser que compara la contraseña
        # recibida (en texto plano) contra el hash guardado en el campo 'password'.
        # Antes se llamaba a la función suelta check_password(contrasena, usuario.contrasena_hash).
        # Ahora el propio objeto sabe dónde está su hash, por eso se llama sobre la instancia.
        if usuario is None or not usuario.check_password(contrasena):
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


class UsuarioUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_usuario_o_error(self, request, pk):
        es_admin = request.user.tipo_rol == Usuario.TipoRol.ADMINISTRADOR
        if not es_admin and request.user.pk != pk:
            return None, Response(
                {'detail': 'No tienes permiso para acceder a este perfil.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            return Usuario.objects.get(pk=pk), None
        except Usuario.DoesNotExist:
            return None, Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        usuario, error = self._get_usuario_o_error(request, pk)
        if error:
            return error
        return Response(UsuarioSerializer(usuario).data)

    def patch(self, request, pk):
        usuario, error = self._get_usuario_o_error(request, pk)
        if error:
            return error
        serializer = UsuarioUpdateSerializer(
            usuario, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            campos_modificados = list(serializer.validated_data.keys())
            serializer.save()
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.UPDATE,
                modulo='usuarios',
                descripcion=(
                    f'Perfil actualizado: ID={usuario.id}, correo={usuario.correo}. '
                    f'Campos modificados: {", ".join(campos_modificados)}. '
                    f'Editado por: {request.user.correo}'
                ),
            )
            return Response(UsuarioSerializer(usuario).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


_RESPUESTA_GENERICA = {
    'mensaje': 'Si el correo está registrado, recibirás un enlace en los próximos minutos.'
}


class OlvidarContrasenaView(APIView):
    permission_classes = [AllowAny]

    _RATE_LIMIT_MAX     = 3
    _RATE_LIMIT_SECONDS = 15 * 60  # 15 minutos

    def post(self, request):
        from django.core.cache import cache

        serializer = OlvidarContrasenaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        correo = serializer.validated_data['correo'].lower()

        # Rate limit por correo: máximo 3 solicitudes cada 15 minutos.
        # Responde igual aunque esté bloqueado para no revelar información.
        cache_key = f'recuperacion_{correo}'
        intentos  = cache.get(cache_key, 0)
        if intentos >= self._RATE_LIMIT_MAX:
            return Response(_RESPUESTA_GENERICA, status=status.HTTP_200_OK)
        cache.set(cache_key, intentos + 1, timeout=self._RATE_LIMIT_SECONDS)

        try:
            usuario = Usuario.objects.get(correo=correo, estado=Usuario.Estado.ACTIVO)
        except Usuario.DoesNotExist:
            # Respuesta genérica: no revelar si el correo existe en el sistema
            return Response(_RESPUESTA_GENERICA, status=status.HTTP_200_OK)

        # Invalidar tokens anteriores pendientes del mismo usuario
        TokenRecuperacion.objects.filter(usuario=usuario, usado=False).update(usado=True)

        token_str = secrets.token_urlsafe(48)
        TokenRecuperacion.objects.create(
            usuario=usuario,
            token=token_str,
            expiracion=timezone.now() + timedelta(minutes=30),
        )

        frontend_url = env_config('FRONTEND_URL', default='http://localhost:5173')
        enlace = f'{frontend_url}/recuperar-contrasena?token={token_str}'

        send_mail(
            subject='Recuperación de contraseña - ABP Platform',
            message=(
                f'Hola {usuario.nombre},\n\n'
                f'Solicitaste restablecer tu contraseña en ABP Platform.\n\n'
                f'Haz clic en el siguiente enlace (válido por 30 minutos):\n\n'
                f'{enlace}\n\n'
                f'Si no solicitaste esto, ignora este correo.\n\n'
                f'ABP Platform - UFPS'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[correo],
            fail_silently=False,
        )

        return Response(_RESPUESTA_GENERICA, status=status.HTTP_200_OK)


class RecuperarContrasenaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecuperarContrasenaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_str        = serializer.validated_data['token']
        nueva_contrasena = serializer.validated_data['nueva_contrasena']

        try:
            token_obj = TokenRecuperacion.objects.select_related('usuario').get(token=token_str)
        except TokenRecuperacion.DoesNotExist:
            return Response(
                {'detail': 'Token inválido o expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token_obj.esta_vigente():
            return Response(
                {'detail': 'Token inválido o expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario = token_obj.usuario
        usuario.set_password(nueva_contrasena)
        usuario.save()

        token_obj.usado = True
        token_obj.save()

        return Response(
            {'mensaje': 'Contraseña actualizada correctamente.'},
            status=status.HTTP_200_OK,
        )