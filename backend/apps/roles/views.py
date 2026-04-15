from django.db.models import Count
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsAdministrador

from .models import Permiso, Rol, RolPermiso
from .serializers import PermisoSerializer, RolListSerializer, RolPermisoSerializer, RolSerializer


class RolListView(ListAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsAdministrador]
    serializer_class = RolListSerializer

    def get_queryset(self):
        return Rol.objects.filter(estado='activo').order_by('nombre')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        usuarios_por_rol = {}
        for rol in queryset:
            count = Usuario.objects.filter(tipo_rol=rol.nombre.lower()).count()
            usuarios_por_rol[rol.id] = count

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'usuarios_por_rol': usuarios_por_rol}
        )
        return Response(serializer.data)


# ──────────────────────────────────────────────
#  ROLES
# ──────────────────────────────────────────────

class RolListCreateView(APIView):
    """
    GET  /api/roles/          — Lista todos los roles.
    POST /api/roles/          — Crea un nuevo rol.
    """
    permission_classes = [EsAdministrador]

    def get(self, request):
        roles = Rol.objects.all().order_by('nombre')
        serializer = RolSerializer(roles, many=True)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='roles',
            descripcion='Consulta de lista de roles',
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = RolSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rol = serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='roles',
            descripcion=f'Rol creado: ID={rol.id}, nombre={rol.nombre}',
        )
        return Response(RolSerializer(rol).data, status=status.HTTP_201_CREATED)


class RolDetailView(APIView):
    """
    GET    /api/roles/{id}/   — Detalle de un rol.
    PUT    /api/roles/{id}/   — Actualización completa de un rol.
    PATCH  /api/roles/{id}/   — Actualización parcial de un rol.
    DELETE /api/roles/{id}/   — Elimina un rol.
    """
    permission_classes = [EsAdministrador]

    def _get_object(self, pk):
        try:
            return Rol.objects.get(pk=pk)
        except Rol.DoesNotExist:
            return None

    def get(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='roles',
            descripcion=f'Consulta de rol: ID={pk}',
        )
        return Response(RolSerializer(rol).data)

    def put(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RolSerializer(rol, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='roles',
            descripcion=f'Rol actualizado: ID={pk}',
        )
        return Response(serializer.data)

    def patch(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RolSerializer(rol, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='roles',
            descripcion=f'Rol actualizado parcialmente: ID={pk}',
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        nombre = rol.nombre
        rol.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='roles',
            descripcion=f'Rol eliminado: ID={pk}, nombre={nombre}',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
#  PERMISOS
# ──────────────────────────────────────────────

class PermisoListCreateView(APIView):
    """
    GET  /api/roles/permisos/   — Lista todos los permisos.
    POST /api/roles/permisos/   — Crea un nuevo permiso.
    """
    permission_classes = [EsAdministrador]

    def get(self, request):
        permisos = Permiso.objects.all().order_by('modulo', 'codigo')
        serializer = PermisoSerializer(permisos, many=True)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='permisos',
            descripcion='Consulta de lista de permisos',
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = PermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        permiso = serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='permisos',
            descripcion=f'Permiso creado: ID={permiso.id}, codigo={permiso.codigo}',
        )
        return Response(PermisoSerializer(permiso).data, status=status.HTTP_201_CREATED)


class PermisoDetailView(APIView):
    """
    GET    /api/roles/permisos/{id}/   — Detalle de un permiso.
    PUT    /api/roles/permisos/{id}/   — Actualización completa de un permiso.
    PATCH  /api/roles/permisos/{id}/   — Actualización parcial de un permiso.
    DELETE /api/roles/permisos/{id}/   — Elimina un permiso.
    """
    permission_classes = [EsAdministrador]

    def _get_object(self, pk):
        try:
            return Permiso.objects.get(pk=pk)
        except Permiso.DoesNotExist:
            return None

    def get(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='permisos',
            descripcion=f'Consulta de permiso: ID={pk}',
        )
        return Response(PermisoSerializer(permiso).data)

    def put(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermisoSerializer(permiso, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='permisos',
            descripcion=f'Permiso actualizado: ID={pk}',
        )
        return Response(serializer.data)

    def patch(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermisoSerializer(permiso, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='permisos',
            descripcion=f'Permiso actualizado parcialmente: ID={pk}',
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        codigo = permiso.codigo
        permiso.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='permisos',
            descripcion=f'Permiso eliminado: ID={pk}, codigo={codigo}',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
#  ROL-PERMISO
# ──────────────────────────────────────────────

class RolPermisoListCreateView(APIView):
    """
    GET  /api/roles/rol-permiso/   — Lista todas las asignaciones rol-permiso.
    POST /api/roles/rol-permiso/   — Asigna un permiso a un rol.
    """
    permission_classes = [EsAdministrador]

    def get(self, request):
        qs = RolPermiso.objects.select_related('rol', 'permiso').all()
        serializer = RolPermisoSerializer(qs, many=True)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='rol_permiso',
            descripcion='Consulta de lista de asignaciones rol-permiso',
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = RolPermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rp = serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='rol_permiso',
            descripcion=f'Permiso asignado: rol={rp.rol.nombre}, permiso={rp.permiso.codigo}',
        )
        return Response(RolPermisoSerializer(rp).data, status=status.HTTP_201_CREATED)


class RolPermisoDetailView(APIView):
    """
    GET    /api/roles/rol-permiso/{id}/   — Detalle de una asignación.
    DELETE /api/roles/rol-permiso/{id}/   — Elimina una asignación rol-permiso.
    """
    permission_classes = [EsAdministrador]

    def _get_object(self, pk):
        try:
            return RolPermiso.objects.select_related('rol', 'permiso').get(pk=pk)
        except RolPermiso.DoesNotExist:
            return None

    def get(self, request, pk):
        rp = self._get_object(pk)
        if rp is None:
            return Response({'detail': 'Asignación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='rol_permiso',
            descripcion=f'Consulta de asignación rol-permiso: ID={pk}',
        )
        return Response(RolPermisoSerializer(rp).data)

    def delete(self, request, pk):
        rp = self._get_object(pk)
        if rp is None:
            return Response({'detail': 'Asignación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        descripcion = f'Permiso removido: rol={rp.rol.nombre}, permiso={rp.permiso.codigo}'
        rp.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='rol_permiso',
            descripcion=descripcion,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)