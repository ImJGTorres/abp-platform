from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.actividades.models import Actividad
from apps.bitacora.models import BitacoraSistema
from apps.equipos.models import MiembroEquipo
from apps.usuarios.authentication import UsuarioJWTAuthentication

from .models import Entregable
from .serializers import EntregableCreateSerializer, EntregableSerializer


class EntregableListCreateView(generics.ListCreateAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EntregableCreateSerializer
        return EntregableSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['actividad'] = get_object_or_404(Actividad, pk=self.kwargs['id_actividad'])
        return ctx

    def get_queryset(self):
        actividad_id = self.kwargs['id_actividad']
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        usuario = self.request.user
        tipo_rol = usuario.tipo_rol

        proyecto = actividad.id_fase.id_proyecto

        if tipo_rol == 'docente':
            if proyecto.id_curso.id_docente_id != usuario.id:
                raise PermissionDenied('No tienes acceso a este proyecto.')
        else:
            es_miembro = MiembroEquipo.objects.filter(
                usuario=usuario,
                equipo__proyecto=proyecto,
                estado='activo',
            ).exists()
            if not es_miembro:
                raise PermissionDenied('No perteneces a este proyecto.')

        return Entregable.objects.filter(id_actividad=actividad).order_by('-fecha_creacion')

    def perform_create(self, serializer):
        actividad_id = self.kwargs['id_actividad']
        actividad = get_object_or_404(Actividad, pk=actividad_id)
        usuario = self.request.user

        proyecto = actividad.id_fase.id_proyecto
        miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo__proyecto=proyecto,
            estado='activo',
        ).select_related('equipo').first()

        if not miembro:
            raise PermissionDenied('No perteneces a un equipo en este proyecto.')

        with transaction.atomic():
            entregable = serializer.save(
                id_actividad=actividad,
                id_equipo=miembro.equipo,
                estado='borrador',
            )
            self._entregable_creado = entregable
            try:
                BitacoraSistema.objects.create(
                    id_usuario=usuario,
                    nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                    accion='CREATE',
                    modulo='Entregables',
                    descripcion=f'Entregable "{entregable.titulo}" creado para actividad {actividad_id}',
                    ip_origen=self.request.META.get('REMOTE_ADDR'),
                )
            except Exception:
                pass

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(EntregableSerializer(self._entregable_creado).data, status=status.HTTP_201_CREATED)


class EnviarEntregableView(generics.UpdateAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch']

    def get_object(self):
        entregable = get_object_or_404(Entregable, pk=self.kwargs['pk'])
        usuario = self.request.user

        es_miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo=entregable.id_equipo,
            estado='activo',
        ).exists()
        if not es_miembro:
            raise PermissionDenied('No perteneces al equipo dueño de este entregable.')

        if entregable.estado != 'borrador':
            raise ValidationError('Solo se puede enviar un entregable en estado borrador.')

        return entregable

    def patch(self, request, *args, **kwargs):
        entregable = self.get_object()
        usuario = request.user

        with transaction.atomic():
            entregable.estado = 'enviado'
            entregable.fecha_envio = timezone.now()
            entregable.save(update_fields=['estado', 'fecha_envio'])
            try:
                BitacoraSistema.objects.create(
                    id_usuario=usuario,
                    nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                    accion='UPDATE',
                    modulo='Entregables',
                    descripcion=f'Entregable {entregable.id} enviado para revisión',
                    ip_origen=request.META.get('REMOTE_ADDR'),
                )
            except Exception:
                pass

        return Response(EntregableSerializer(entregable).data, status=status.HTTP_200_OK)
