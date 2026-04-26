<<<<<<< HEAD
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
=======
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.cursos.models import Proyecto
from apps.usuarios.models import Usuario
from .models import Equipo, MiembroEquipo
from .serializers import EquipoDetalleSerializer, EstudianteDisponibleSerializer


class EquiposPorProyectoView(APIView):
    """GET /api/proyectos/<proyecto_id>/equipos/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.select_related('id_curso').get(pk=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response({'detail': 'Proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        equipos_qs = Equipo.objects.filter(proyecto=proyecto).prefetch_related('miembros__usuario')
        equipos_data = EquipoDetalleSerializer(equipos_qs, many=True).data

        return Response({
            'proyecto': {'id': proyecto.id, 'nombre': proyecto.nombre},
            'curso': {
                'id':     proyecto.id_curso.id,
                'nombre': proyecto.id_curso.nombre,
                'codigo': proyecto.id_curso.codigo,
            },
            'equipos':              equipos_data,
            'cantidad_equipos':     len(equipos_data),
            'cantidad_estudiantes': sum(e['cantidad_miembros'] for e in equipos_data),
        })


class EstudiantesEquipoView(APIView):
    """GET /api/equipos/<equipo_id>/estudiantes/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, equipo_id):
        try:
            equipo = Equipo.objects.select_related('proyecto').get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        proyecto = equipo.proyecto

        # IDs ya asignados a ESTE equipo (activos)
        ids_en_equipo = set(
            MiembroEquipo.objects.filter(equipo=equipo, estado='activo')
            .values_list('usuario_id', flat=True)
        )

        # IDs asignados a OTRO equipo del mismo proyecto (activos)
        ids_otro_equipo = set(
            MiembroEquipo.objects.filter(equipo__proyecto=proyecto, estado='activo')
            .exclude(equipo=equipo)
            .values_list('usuario_id', flat=True)
        )

        todos = Usuario.objects.filter(tipo_rol='estudiante', estado='activo').order_by('nombre', 'apellido')

        disponibles    = []
        ya_en_equipo   = []
        en_otro_equipo = []

        for est in todos:
            if est.id in ids_en_equipo:
                ya_en_equipo.append(est)
            elif est.id in ids_otro_equipo:
                en_otro_equipo.append(est)
            else:
                disponibles.append(est)

        ser = EstudianteDisponibleSerializer

        return Response({
            'equipo': {
                'id':          equipo.id,
                'nombre':      equipo.nombre,
                'cupo_maximo': equipo.cupo_maximo,
            },
            'cantidad_miembros': len(ids_en_equipo),
            'disponibles':       ser(disponibles, many=True).data,
            'ya_en_equipo':      ser(ya_en_equipo, many=True).data,
            'en_otro_equipo':    ser(en_otro_equipo, many=True).data,
        })


class AsignarEstudiantesView(APIView):
    """POST /api/equipos/<equipo_id>/asignar/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, equipo_id):
        try:
            equipo = Equipo.objects.get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        usuario_ids = request.data.get('usuarios', [])
        if not usuario_ids:
            return Response({'detail': 'No se proporcionaron usuarios.'}, status=status.HTTP_400_BAD_REQUEST)

        asignados = 0
        errores   = []

        for uid in usuario_ids:
            try:
                usuario = Usuario.objects.get(pk=uid, tipo_rol='estudiante')
            except Usuario.DoesNotExist:
                errores.append({'usuario_id': uid, 'error': 'Estudiante no encontrado.'})
                continue

            if MiembroEquipo.objects.filter(equipo=equipo, usuario=usuario, estado='activo').exists():
                continue  # ya estaba, no es error

            if MiembroEquipo.objects.filter(
                equipo__proyecto=equipo.proyecto, usuario=usuario, estado='activo'
            ).exists():
                errores.append({'usuario_id': uid, 'error': 'Ya pertenece a otro equipo de este proyecto.'})
                continue

            miembros_activos = MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count()
            if miembros_activos >= equipo.cupo_maximo:
                errores.append({'usuario_id': uid, 'error': 'El equipo ha alcanzado su cupo máximo.'})
                continue

            MiembroEquipo.objects.create(equipo=equipo, usuario=usuario)
            asignados += 1

        return Response({'asignados': asignados, 'errores': errores}, status=status.HTTP_200_OK)
>>>>>>> develop
