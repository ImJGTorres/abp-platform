import io

from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.cursos.models import Proyecto
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsDocente
from .models import Equipo, MiembroEquipo
from .serializers import (
    ActualizarRolSerializer,
    EquipoCreateSerializer,
    EquipoDetalleSerializer,
    EquipoListSerializer,
    EquipoSerializer,
    EquipoUpdateSerializer,
    EstudianteDisponibleSerializer,
    MiembroEquipoSerializer,
    UsuarioResumenSerializer,
)


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


# ---------------------------------------------------------------------------
# Equipos por proyecto
# ---------------------------------------------------------------------------

class EquiposPorProyectoView(APIView):
    """
    GET  /api/proyectos/<proyecto_id>/equipos/  — Lista equipos del proyecto con detalle.
    POST /api/proyectos/<proyecto_id>/equipos/  — Crea un nuevo equipo en el proyecto.
    """
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

    def post(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.select_related('id_curso').get(pk=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response({'detail': 'Proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EquipoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            equipo = serializer.save(proyecto=proyecto)
            equipo_con_miembros = Equipo.objects.prefetch_related('miembros__usuario').get(pk=equipo.pk)
            return Response(EquipoDetalleSerializer(equipo_con_miembros).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProyectoEquiposView(APIView):
    """
    GET  /api/proyectos/<proyecto_id>/equipos/  — Lista equipos filtrada por rol del usuario.
    POST /api/proyectos/<proyecto_id>/equipos/  — Crea un equipo (solo docente).
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def get(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response({"detail": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

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
                usuario=user, equipo__proyecto=proyecto, estado='activo'
            ).first()
            equipos = Equipo.objects.filter(id=membresia.equipo.id) if membresia else Equipo.objects.none()

        serializer = EquipoListSerializer(equipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, proyecto_id):
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
        except Proyecto.DoesNotExist:
            return Response({"detail": "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EquipoCreateSerializer(data=request.data, context={'proyecto': proyecto})
        if serializer.is_valid():
            try:
                equipo = serializer.save()
            except IntegrityError:
                return Response(
                    {"detail": "Ya existe un equipo con ese nombre en este proyecto."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ip = get_client_ip(request)
            registrar_bitacora(
                request.user,
                BitacoraSistema.Accion.CREATE,
                'equipos',
                f"Crear equipo '{equipo.nombre}' en proyecto {proyecto.nombre}",
                ip,
            )
            return Response(EquipoSerializer(equipo).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Estudiantes del equipo
# ---------------------------------------------------------------------------

class EstudiantesEquipoView(APIView):
    """GET /api/equipos/<equipo_id>/estudiantes/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, equipo_id):
        try:
            equipo = Equipo.objects.select_related('proyecto').get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        proyecto = equipo.proyecto

        ids_en_equipo = set(
            MiembroEquipo.objects.filter(equipo=equipo, estado='activo')
            .values_list('usuario_id', flat=True)
        )
        ids_otro_equipo = set(
            MiembroEquipo.objects.filter(equipo__proyecto=proyecto, estado='activo')
            .exclude(equipo=equipo)
            .values_list('usuario_id', flat=True)
        )

        todos = Usuario.objects.filter(tipo_rol='estudiante', estado='activo').order_by('nombre', 'apellido')
        disponibles, ya_en_equipo, en_otro_equipo = [], [], []

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


# ---------------------------------------------------------------------------
# Asignar estudiantes al equipo
# ---------------------------------------------------------------------------

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
        errores = []

        for uid in usuario_ids:
            try:
                usuario = Usuario.objects.get(pk=uid, tipo_rol='estudiante')
            except Usuario.DoesNotExist:
                errores.append({'usuario_id': uid, 'error': 'Estudiante no encontrado.'})
                continue

            if MiembroEquipo.objects.filter(equipo=equipo, usuario=usuario, estado='activo').exists():
                continue

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


# ---------------------------------------------------------------------------
# Miembros del equipo
# ---------------------------------------------------------------------------

class MiembroListView(generics.ListAPIView):
    """GET /api/equipos/<equipo_id>/miembros/"""
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = MiembroEquipoSerializer

    def get_queryset(self):
        equipo_id = self.kwargs['equipo_id']
        get_object_or_404(Equipo, pk=equipo_id)
        return MiembroEquipo.objects.filter(
            equipo_id=equipo_id, estado='activo'
        ).select_related('usuario')

    def post(self, request, equipo_id):
        equipo = get_object_or_404(Equipo, pk=equipo_id)

        estudiante_id = request.data.get('estudiante_id')
        if not estudiante_id:
            return Response({'detail': 'Se requiere estudiante_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            estudiante = Usuario.objects.get(pk=estudiante_id, tipo_rol='estudiante', estado='activo')
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Estudiante no encontrado o no es un estudiante activo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if MiembroEquipo.objects.filter(equipo=equipo, usuario=estudiante, estado='activo').exists():
            return Response({'detail': 'El estudiante ya es miembro de este equipo.'}, status=status.HTTP_400_BAD_REQUEST)

        if MiembroEquipo.objects.filter(
            usuario=estudiante, estado='activo', equipo__proyecto=equipo.proyecto
        ).exclude(equipo=equipo).exists():
            return Response(
                {'detail': 'El estudiante ya pertenece a otro equipo en este proyecto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count() >= equipo.cupo_maximo:
            return Response({'detail': 'El equipo ha alcanzado su cupo máximo.'}, status=status.HTTP_400_BAD_REQUEST)

        miembro = MiembroEquipo.objects.create(equipo=equipo, usuario=estudiante)
        try:
            BitacoraSistema.objects.create(
                accion=BitacoraSistema.Accion.CREATE,
                modulo='miembros_equipo',
                descripcion=f'Estudiante {estudiante.id} asignado al equipo {equipo.id}',
            )
        except Exception:
            pass

        return Response({
            'id':                 miembro.id,
            'equipo_id':          miembro.equipo.id,
            'estudiante_id':      miembro.usuario.id,
            'nombre_estudiante':  f"{miembro.usuario.nombre} {miembro.usuario.apellido}".strip(),
            'fecha_ingreso':      miembro.fecha_asignacion,
        }, status=status.HTTP_201_CREATED)


class RetirarMiembroView(generics.GenericAPIView):
    """DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/"""
    authentication_classes = [UsuarioJWTAuthentication]

    def delete(self, request, equipo_id, usuario_id):
        miembro = get_object_or_404(MiembroEquipo, equipo_id=equipo_id, usuario_id=usuario_id, estado='activo')
        miembro.estado = 'retirado'
        miembro.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActualizarRolView(generics.UpdateAPIView):
    """PATCH /api/equipos/<equipo_id>/miembros/<usuario_id>/rol/"""
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = ActualizarRolSerializer
    http_method_names = ['patch']

    def get_object(self):
        return get_object_or_404(
            MiembroEquipo,
            equipo_id=self.kwargs['equipo_id'],
            usuario_id=self.kwargs['usuario_id'],
            estado='activo',
        )

    def patch(self, request, *args, **kwargs):
        miembro = self.get_object()
        if request.user.id != miembro.usuario_id:
            return Response({'detail': 'Solo puedes actualizar tu propio rol.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(miembro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Estudiantes del curso
# ---------------------------------------------------------------------------

class EstudiantesCursoView(APIView):
    """GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>"""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, curso_id):
        proyecto_id = request.query_params.get('proyecto_id')

        if proyecto_id:
            proyecto = get_object_or_404(Proyecto, pk=proyecto_id, id_curso_id=curso_id)
            ya_asignados = MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto, estado='activo'
            ).values_list('usuario_id', flat=True)
            estudiantes = Usuario.objects.filter(
                tipo_rol='estudiante', estado='activo'
            ).exclude(id__in=ya_asignados).order_by('nombre', 'apellido')
            return Response(UsuarioResumenSerializer(estudiantes, many=True).data)

        membresias = MiembroEquipo.objects.filter(
            equipo__proyecto__id_curso_id=curso_id, estado='activo'
        ).select_related('usuario', 'equipo', 'equipo__proyecto')

        usuario_equipos = {}
        for m in membresias:
            uid = m.usuario_id
            if uid not in usuario_equipos:
                usuario_equipos[uid] = []
            usuario_equipos[uid].append({
                'equipo_id':       m.equipo.id,
                'equipo_nombre':   m.equipo.nombre,
                'proyecto_id':     m.equipo.proyecto.id,
                'proyecto_nombre': m.equipo.proyecto.nombre,
            })

        todos = Usuario.objects.filter(tipo_rol='estudiante', estado='activo').order_by('nombre', 'apellido')
        disponibles, en_equipo = [], []

        for est in todos:
            data = {
                'id':                est.id,
                'nombre':            est.nombre,
                'apellido':          est.apellido,
                'correo':            est.correo,
                'codigo_estudiante': est.codigo_estudiante or '',
            }
            if est.id in usuario_equipos:
                data['equipos'] = usuario_equipos[est.id]
                en_equipo.append(data)
            else:
                disponibles.append(data)

        return Response({'disponibles': disponibles, 'en_equipo': en_equipo})


class EstudiantesDisponiblesView(generics.ListAPIView):
    """GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int> (backwards compat)"""
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = UsuarioResumenSerializer

    def get_queryset(self):
        curso_id = self.kwargs['curso_id']
        proyecto_id = self.request.query_params.get('proyecto_id')
        if not proyecto_id:
            raise ValidationError("Se requiere el parámetro proyecto_id.")
        proyecto = get_object_or_404(Proyecto, pk=proyecto_id, id_curso_id=curso_id)
        ya_asignados = MiembroEquipo.objects.filter(
            equipo__proyecto=proyecto, estado='activo'
        ).values_list('usuario_id', flat=True)
        return Usuario.objects.filter(tipo_rol='estudiante', estado='activo').exclude(id__in=ya_asignados)


# ---------------------------------------------------------------------------
# Actualizar equipo (HU-010)
# ---------------------------------------------------------------------------

class EquipoUpdateView(APIView):
    """PUT /api/equipos/<equipo_id>/"""
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def put(self, request, equipo_id):
        try:
            equipo = Equipo.objects.get(id=equipo_id)
        except Equipo.DoesNotExist:
            return Response({"detail": "Equipo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EquipoUpdateSerializer(equipo, data=request.data, partial=False)
        if serializer.is_valid():
            nuevo_nombre = serializer.validated_data.get('nombre')
            nueva_capacidad = serializer.validated_data.get('capacidad_maxima')

            if nuevo_nombre and nuevo_nombre != equipo.nombre:
                if Equipo.objects.filter(proyecto=equipo.proyecto, nombre=nuevo_nombre).exclude(id=equipo.id).exists():
                    return Response(
                        {"detail": "Ya existe un equipo con ese nombre en este proyecto."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if nueva_capacidad is not None:
                miembros_actuales = equipo.miembros.filter(estado='activo').count()
                if nueva_capacidad < miembros_actuales:
                    return Response(
                        {"detail": f"La nueva capacidad ({nueva_capacidad}) no puede ser menor al número de miembros actuales ({miembros_actuales})."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            equipo = serializer.save()
            ip = get_client_ip(request)
            registrar_bitacora(
                request.user,
                BitacoraSistema.Accion.UPDATE,
                'equipos',
                f"Actualizar equipo '{equipo.nombre}' (ID: {equipo.id})",
                ip,
            )
            return Response(EquipoSerializer(equipo).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
