from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer
from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento


class UsuarioCreateView(generics.CreateAPIView):
    queryset         = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [AllowAny]  # TODO: cambiar a IsAdminUser cuando esté el JWT

    def perform_create(self, serializer):
        usuario_creado = serializer.save()      # 1. guarda el usuario en BD
        registrar_evento(                        # 2. registra en bitácora (ST-08)
            request=self.request,               # ← saca la IP y el admin automáticamente
            accion=BitacoraSistema.Accion.CREATE,
            modulo='usuarios',
            descripcion=f'Usuario creado: ID={usuario_creado.id}, correo={usuario_creado.correo}',
        )
