from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.cursos.models import Proyecto
from apps.equipos.models import Equipo, MiembroEquipo
from apps.equipos.serializers import (
    EquipoCreateSerializer,
    EquipoListSerializer,
    EquipoSerializer,
    EquipoUpdateSerializer,
)
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsDocente


def registrar_bitacora(usuario, accion, modulo, descripcion=None, ip=None):
    try:
        BitacoraSistema.objects.create(
            id_usuario=usuario,
            nombre_usuario=f"{usuario.nombre} {usuario.apellido}",
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip_origen=ip,
        )
    except Exception:
        pass


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ProyectoEquiposView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def get(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response(
                {"detail": "Proyecto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        es_docente_o_director = user.tipo_rol in [
            Usuario.TipoRol.DOCENTE,
            Usuario.TipoRol.DIRECTOR,
            Usuario.TipoRol.ADMINISTRADOR,
        ]

        if es_docente_o_director:
            equipos = Equipo.objects.filter(proyecto=proyecto)
        else:
            membresia = MiembroEquipo.objects.filter(
                usuario=user,
                equipo__proyecto=proyecto,
                estado='activo'
            ).first()
            if membresia:
                equipos = Equipo.objects.filter(id=membresia.equipo.id)
            else:
                equipos = Equipo.objects.none()

        serializer = EquipoListSerializer(equipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response(
                {"detail": "Proyecto no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EquipoCreateSerializer(data=request.data, context={'proyecto': proyecto})
        if serializer.is_valid():
            try:
                equipo = serializer.save()
            except IntegrityError:
                return Response(
                    {"detail": "Ya existe un equipo con ese nombre en este proyecto."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ip = get_client_ip(request)
            registrar_bitacora(
                request.user,
                BitacoraSistema.Accion.CREATE,
                'equipos',
                f"Crear equipo '{equipo.nombre}' en proyecto {proyecto.nombre}",
                ip
            )

            return Response(EquipoSerializer(equipo).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EquipoUpdateView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def put(self, request, equipo_id):
        try:
            equipo = Equipo.objects.get(id=equipo_id)
        except Equipo.DoesNotExist:
            return Response(
                {"detail": "Equipo no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EquipoUpdateSerializer(equipo, data=request.data, partial=False)
        if serializer.is_valid():
            nuevo_nombre = serializer.validated_data.get('nombre')
            nueva_capacidad = serializer.validated_data.get('capacidad_maxima')

            if nuevo_nombre and nuevo_nombre != equipo.nombre:
                if Equipo.objects.filter(proyecto=equipo.proyecto, nombre=nuevo_nombre).exclude(id=equipo.id).exists():
                    return Response(
                        {"detail": "Ya existe un equipo con ese nombre en este proyecto."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if nueva_capacidad is not None:
                miembros_actuales = equipo.miembros.filter(estado='activo').count()
                if nueva_capacidad < miembros_actuales:
                    return Response(
                        {"detail": f"La nueva capacidad ({nueva_capacidad}) no puede ser menor al número de miembros actuales ({miembros_actuales})."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            equipo = serializer.save()

            ip = get_client_ip(request)
            registrar_bitacora(
                request.user,
                BitacoraSistema.Accion.UPDATE,
                'equipos',
                f"Actualizar equipo '{equipo.nombre}' (ID: {equipo.id})",
                ip
            )

            return Response(EquipoSerializer(equipo).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
