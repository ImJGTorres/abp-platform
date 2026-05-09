import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cursos.models import Actividad
from apps.bitacora.models import BitacoraSistema
from apps.equipos.models import MiembroEquipo
from apps.usuarios.authentication import UsuarioJWTAuthentication

from .models import ArchivoAdjunto, Entregable, EntregableVersion
from .serializers import (
    ArchivoAdjuntoSerializer,
    EntregableCreateSerializer,
    EntregableSerializer,
    EntregableVersionDetalleSerializer,
    SubirArchivoSerializer,
)
from .services import crear_nueva_version


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


class ArchivoListCreateView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubirArchivoSerializer
        return ArchivoAdjuntoSerializer

    def get(self, request, id_entregable):
        entregable = get_object_or_404(Entregable, pk=id_entregable)
        usuario = request.user
        tipo_rol = usuario.tipo_rol
        proyecto = entregable.id_actividad.id_fase.id_proyecto

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

        archivos = ArchivoAdjunto.objects.filter(id_entregable=entregable)
        serializer = ArchivoAdjuntoSerializer(archivos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id_entregable):
        entregable = get_object_or_404(Entregable, pk=id_entregable)
        usuario = request.user

        es_miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo=entregable.id_equipo,
            estado='activo',
        ).exists()
        if not es_miembro:
            raise PermissionDenied('No perteneces al equipo dueño de este entregable.')

        serializer = SubirArchivoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        archivo = serializer.validated_data['archivo']
        tipo_mime = getattr(archivo, '_tipo_mime', archivo.content_type)

        ext = archivo.name.rsplit('.', 1)[-1].lower()
        nombre_uuid = f"{uuid.uuid4().hex}.{ext}"
        ruta_relativa = f"entregables/archivos/{nombre_uuid}"

        default_storage.save(ruta_relativa, ContentFile(archivo.read()))

        with transaction.atomic():
            adjunto = ArchivoAdjunto(
                id_entregable=entregable,
                id_usuario=usuario,
                nombre_original=archivo.name,
                nombre_almacenado=nombre_uuid,
                ruta=ruta_relativa,
                tipo_mime=tipo_mime,
                tamaño_bytes=archivo.size,
            )
            adjunto.save()

            try:
                BitacoraSistema.objects.create(
                    id_usuario=usuario,
                    nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                    accion='CREATE',
                    modulo='Archivos',
                    descripcion=f'Archivo "{archivo.name}" subido al entregable {id_entregable}',
                    ip_origen=request.META.get('REMOTE_ADDR'),
                )
            except Exception:
                pass

        return Response(ArchivoAdjuntoSerializer(adjunto, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ArchivoAdjuntoEliminarView(generics.DestroyAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, archivo_id):
        try:
            archivo = ArchivoAdjunto.objects.select_related('id_entregable').get(pk=archivo_id)
        except ArchivoAdjunto.DoesNotExist:
            return Response({'error': 'Archivo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        entregable = archivo.id_entregable
        if entregable.estado != 'borrador':
            return Response(
                {'error': 'Solo se pueden eliminar archivos de entregables en estado borrador.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            ruta = archivo.ruta
            nombre_original = archivo.nombre_original
            entregable_id = entregable.id
            archivo.delete()

            if default_storage.exists(ruta):
                default_storage.delete(ruta)

            try:
                BitacoraSistema.objects.create(
                    id_usuario=request.user,
                    nombre_usuario=f'{request.user.nombre} {request.user.apellido}',
                    accion='DELETE',
                    modulo='Archivos',
                    descripcion=f'Archivo "{nombre_original}" eliminado del entregable {entregable_id}',
                    ip_origen=request.META.get('REMOTE_ADDR'),
                )
            except Exception:
                pass

        return Response(status=status.HTTP_204_NO_CONTENT)


class NuevaVersionEntregableView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        entregable = get_object_or_404(Entregable, pk=pk)
        usuario = request.user

        if entregable.estado != 'rechazado':
            raise ValidationError('Solo se puede crear una nueva versión de un entregable rechazado.')

        es_miembro = MiembroEquipo.objects.filter(
            usuario=usuario,
            equipo=entregable.id_equipo,
            estado='activo',
        ).exists()
        if not es_miembro:
            raise PermissionDenied('No perteneces al equipo dueño de este entregable.')

        if usuario.tipo_rol != 'estudiante':
            raise PermissionDenied('Solo los estudiantes pueden crear nuevas versiones.')

        motivo = request.data.get('motivo_revision', '')

        with transaction.atomic():
            nuevo_entregable = crear_nueva_version(entregable, usuario, motivo)

        return Response(EntregableSerializer(nuevo_entregable).data, status=status.HTTP_201_CREATED)


class HistorialVersionesView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _obtener_original(self, entregable):
        actual = entregable
        while actual.id_version_anterior_id is not None:
            actual = actual.id_version_anterior
        return actual

    def get(self, request, pk):
        entregable = get_object_or_404(Entregable, pk=pk)
        usuario = request.user
        tipo_rol = usuario.tipo_rol

        proyecto = entregable.id_actividad.id_fase.id_proyecto

        if tipo_rol == 'docente':
            if proyecto.id_curso.id_docente_id != usuario.id:
                raise PermissionDenied('No tienes acceso a este proyecto.')
        else:
            es_miembro = MiembroEquipo.objects.filter(
                usuario=usuario,
                equipo=entregable.id_equipo,
                estado='activo',
            ).exists()
            if not es_miembro:
                raise PermissionDenied('No perteneces al equipo dueño de este entregable.')

        original = self._obtener_original(entregable)

        versiones_qs = EntregableVersion.objects.filter(
            id_entregable_original=original,
        ).select_related('id_version').order_by('numero_version')

        if not versiones_qs.exists():
            # El entregable no tiene historial en la tabla; construir respuesta mínima
            data = [{
                'numero_version': original.numero_version,
                'id_entregable': original.id,
                'estado': original.estado,
                'fecha_creacion': original.fecha_creacion,
                'fecha_envio': original.fecha_envio,
                'motivo_revision': '',
                'archivos': ArchivoAdjuntoSerializer(
                    original.archivos.all(), many=True, context={'request': request}
                ).data,
                'retroalimentacion': getattr(original, 'retroalimentacion', None),
            }]
            return Response(data, status=status.HTTP_200_OK)

        serializer = EntregableVersionDetalleSerializer(
            versiones_qs, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
