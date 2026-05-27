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
from rest_framework.views import APIView

from apps.cursos.models import Actividad
from apps.bitacora.models import BitacoraSistema
from apps.equipos.models import MiembroEquipo
from apps.usuarios.authentication import UsuarioJWTAuthentication

from .models import ArchivoAdjunto, Entregable, EntregableVersion, Notificacion
from .serializers import (
    ArchivoAdjuntoSerializer,
    EntregableCreateSerializer,
    EntregablePendienteSerializer,
    EntregableSerializer,
    EntregableValidacionSerializer,
    EntregableVersionDetalleSerializer,
    NotificacionSerializer,
    SubirArchivoSerializer,
    ValidarEntregableSerializer,
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

        if usuario.tipo_rol not in ('estudiante', 'lider_equipo'):
            raise PermissionDenied('Solo los estudiantes pueden crear nuevas versiones.')

        motivo = request.data.get('motivo_revision', '')

        with transaction.atomic():
            nuevo_entregable = crear_nueva_version(entregable, usuario, motivo)

        return Response(EntregableSerializer(nuevo_entregable).data, status=status.HTTP_201_CREATED)


class ValidarEntregableView(generics.GenericAPIView):
    """PATCH /api/entregables/<pk>/validar/ — docente aprueba o rechaza un entregable."""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        entregable = get_object_or_404(Entregable, pk=pk)
        usuario = request.user

        if usuario.tipo_rol != 'docente':
            raise PermissionDenied('Solo los docentes pueden validar entregables.')

        proyecto = entregable.id_actividad.id_fase.id_proyecto
        if proyecto.id_curso.id_docente_id != usuario.id:
            raise PermissionDenied('No eres el docente de este proyecto.')

        if entregable.estado != 'enviado':
            raise ValidationError('Solo se pueden validar entregables en estado "enviado".')

        serializer = ValidarEntregableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        accion = serializer.validated_data['accion']
        retroalimentacion = serializer.validated_data.get('retroalimentacion', '')

        nuevo_estado = 'aprobado' if accion == 'aprobar' else 'rechazado'

        with transaction.atomic():
            entregable.estado = nuevo_estado
            entregable.retroalimentacion = retroalimentacion
            entregable.id_docente_validador = usuario
            entregable.fecha_validacion = timezone.now()
            entregable.save(update_fields=['estado', 'retroalimentacion', 'id_docente_validador', 'fecha_validacion'])

            miembros = entregable.id_equipo.miembros.filter(estado='activo').select_related('usuario')
            notificaciones = [
                Notificacion(
                    id_usuario_destino=m.usuario,
                    tipo=nuevo_estado,
                    titulo_entregable=entregable.titulo,
                    retroalimentacion=retroalimentacion,
                    id_entregable=entregable,
                )
                for m in miembros
            ]
            if notificaciones:
                Notificacion.objects.bulk_create(notificaciones)

            from apps.entregables.services import registrar_validacion_bitacora
            accion_bitacora = 'APROBAR_ENTREGABLE' if accion == 'aprobar' else 'RECHAZAR_ENTREGABLE'
            registrar_validacion_bitacora(entregable, usuario, accion_bitacora)

        return Response(EntregableSerializer(entregable).data, status=status.HTTP_200_OK)


class NotificacionesView(generics.ListAPIView):
    """GET /api/notificaciones/ — notificaciones del usuario autenticado."""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(id_usuario_destino=self.request.user)


class MarcarNotificacionLeidaView(generics.GenericAPIView):
    """PATCH /api/notificaciones/<pk>/leer/ — marca como leída."""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notificacion = get_object_or_404(Notificacion, pk=pk, id_usuario_destino=request.user)
        notificacion.leida = True
        notificacion.save(update_fields=['leida'])
        return Response(NotificacionSerializer(notificacion).data, status=status.HTTP_200_OK)


class MarcarTodasLeidasView(generics.GenericAPIView):
    """PATCH /api/notificaciones/leer-todas/ — marca todas las notificaciones como leídas."""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        Notificacion.objects.filter(id_usuario_destino=request.user, leida=False).update(leida=True)
        return Response({'detail': 'Todas las notificaciones marcadas como leídas.'}, status=status.HTTP_200_OK)


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


# HU-022 — Validación de entregables por docente
def _solo_docente(usuario):
    """Retorna True si el usuario tiene rol Docente."""
    return usuario.tipo_rol == 'docente'


class EntregableAprobarView(APIView):
    """BE-01: PATCH /api/entregables/:id/aprobar/"""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, entregable_id):
        usuario = request.user
        if not _solo_docente(usuario):
            return Response(
                {'error': 'Solo los docentes pueden aprobar entregables.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            entregable = Entregable.objects.get(pk=entregable_id)
        except Entregable.DoesNotExist:
            return Response({'error': 'Entregable no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if entregable.estado != 'enviado':
            return Response(
                {'error': 'Solo se pueden aprobar entregables en estado enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        retroalimentacion = request.data.get('retroalimentacion', '')

        with transaction.atomic():
            entregable.estado = 'aprobado'
            entregable.retroalimentacion = retroalimentacion
            entregable.id_docente_validador_id = usuario.id
            entregable.fecha_validacion = timezone.now()
            entregable.save(update_fields=[
                'estado', 'retroalimentacion', 'id_docente_validador_id', 'fecha_validacion'
            ])

            try:
                BitacoraSistema.objects.create(
                    nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                    accion='UPDATE',
                    modulo='entregables',
                    descripcion=f'Entregable {entregable_id} aprobado por docente.',
                    id_usuario=usuario,
                )
            except Exception:
                pass

        serializer = EntregableValidacionSerializer(entregable)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EntregableRechazarView(APIView):
    """BE-02: PATCH /api/entregables/:id/rechazar/"""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, entregable_id):
        usuario = request.user
        if not _solo_docente(usuario):
            return Response(
                {'error': 'Solo los docentes pueden rechazar entregables.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            entregable = Entregable.objects.get(pk=entregable_id)
        except Entregable.DoesNotExist:
            return Response({'error': 'Entregable no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if entregable.estado != 'enviado':
            return Response(
                {'error': 'Solo se pueden rechazar entregables en estado enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        retroalimentacion = request.data.get('retroalimentacion', '').strip()
        if not retroalimentacion:
            return Response(
                {'error': 'La retroalimentación es obligatoria al rechazar un entregable.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            entregable.estado = 'rechazado'
            entregable.retroalimentacion = retroalimentacion
            entregable.id_docente_validador_id = usuario.id
            entregable.fecha_validacion = timezone.now()
            entregable.save(update_fields=[
                'estado', 'retroalimentacion', 'id_docente_validador_id', 'fecha_validacion'
            ])

            try:
                BitacoraSistema.objects.create(
                    nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                    accion='UPDATE',
                    modulo='entregables',
                    descripcion=f'Entregable {entregable_id} rechazado por docente.',
                    id_usuario=usuario,
                )
            except Exception:
                pass

        serializer = EntregableValidacionSerializer(entregable)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EntregablesPendientesView(APIView):
    """BE-03: GET /api/proyectos/:id/entregables-pendientes/"""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, proyecto_id):
        usuario = request.user
        if not _solo_docente(usuario):
            return Response(
                {'error': 'Solo los docentes pueden ver entregables pendientes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Filtrar entregables en estado 'enviado' que pertenezcan al proyecto
        # Cadena: entregable → actividad → fase_proyecto → proyecto
        entregables = Entregable.objects.filter(
            estado='enviado',
            id_actividad__id_fase__id_proyecto_id=proyecto_id
        ).select_related('id_equipo', 'id_actividad').order_by('id_actividad__nombre', 'id_equipo__nombre')

        serializer = EntregablePendienteSerializer(entregables, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
