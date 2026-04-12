from django.contrib.auth.hashers import check_password
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        correo    = request.data.get('correo', '').strip()
        contrasena = request.data.get('contrasena', '')

        if not correo or not contrasena:
            return Response(
                {'detail': 'correo y contrasena son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            usuario = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            usuario = None

        if usuario is None or not check_password(contrasena, usuario.contrasena_hash):
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

        refresh = RefreshToken()
        refresh['user_id']   = usuario.id
        refresh['nombre']    = usuario.nombre
        refresh['correo']    = usuario.correo
        refresh['tipo_rol']  = usuario.tipo_rol

        request.usuario = usuario
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.LOGIN,
            modulo='autenticacion',
            descripcion=f'Login exitoso: {correo}',
        )

        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class UsuarioCreateView(generics.CreateAPIView):
    queryset         = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        usuario_creado = serializer.save()      # 1. guarda el usuario en BD
        registrar_evento(                        # 2. registra en bitácora (ST-08)
            request=self.request,               # ← saca la IP y el admin automáticamente
            accion=BitacoraSistema.Accion.CREATE,
            modulo='usuarios',
            descripcion=f'Usuario creado: ID={usuario_creado.id}, correo={usuario_creado.correo}',
        )
