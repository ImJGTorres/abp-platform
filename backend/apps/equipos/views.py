from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.usuarios.authentication import UsuarioJWTAuthentication
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
from apps.bitacora.models import BitacoraSistema
from .models import Equipo, MiembroEquipo
from .serializers import (
<<<<<<< HEAD
    EquipoSerializer, EquipoDetalleSerializer, EstudianteDisponibleSerializer,
=======
    ActualizarRolSerializer, EquipoDetalleSerializer, EstudianteDisponibleSerializer,
>>>>>>> feature/HU-012-backend
    MiembroEquipoSerializer, UsuarioResumenSerializer,
)
from apps.usuarios.permissions import EsDocente


<<<<<<< HEAD
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
=======
class EquiposPorProyectoView(APIView):
    """
    GET  /api/proyectos/<proyecto_id>/equipos/  — Lista los equipos del proyecto.
    POST /api/proyectos/<proyecto_id>/equipos/  — Crea un nuevo equipo en el proyecto.
    """
    permission_classes = [IsAuthenticated]
>>>>>>> feature/HU-011-frontend

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

<<<<<<< HEAD
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
=======
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
>>>>>>> feature/HU-011-frontend
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


        return Response({'asignados': asignados, 'errores': errores}, status=status.HTTP_200_OK)



# GET /api/equipos/<equipo_id>/miembros/
# Lista los miembros activos de un equipo específico.
# Incluye el rol interno y fecha de asignación a través del serializer (MiembroEquipoSerializer).
# Retorna para cada miembro sus datos básicos más rol_interno y descripcion_responsabilidades
class MiembroListView(generics.ListAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = MiembroEquipoSerializer

    def get_queryset(self):
        equipo_id = self.kwargs['equipo_id']
        get_object_or_404(Equipo, pk=equipo_id)
        return MiembroEquipo.objects.filter(
            equipo_id=equipo_id,
            estado='activo'
        ).select_related('usuario')

    def post(self, request, equipo_id):
        """
        Asignar un estudiante a un equipo.
        Valida que el estudiante exista, no esté ya en el equipo,
        no pertenezca a otro equipo del mismo proyecto y que el cupo no esté lleno.
        Retorna 201 con la membresía creada.
        """
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
            return Response(
                {'detail': 'El estudiante ya es miembro de este equipo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if MiembroEquipo.objects.filter(
            usuario=estudiante, estado='activo', equipo__proyecto=equipo.proyecto
        ).exclude(equipo=equipo).exists():
            return Response(
                {'detail': 'El estudiante ya pertenece a otro equipo en este proyecto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count() >= equipo.cupo_maximo:
            return Response(
                {'detail': 'El equipo ha alcanzado su cupo máximo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        miembro = MiembroEquipo.objects.create(equipo=equipo, usuario=estudiante)

        # Registro en bitácora de la asignación del estudiante al equipo
        try:
            BitacoraSistema.objects.create(
                accion=BitacoraSistema.Accion.CREATE,
                modulo='miembros_equipo',
                descripcion=f'Estudiante {estudiante.id} asignado al equipo {equipo.id}',
            )
        except Exception:
            pass

        return Response({
            'id': miembro.id,
            'equipo_id': miembro.equipo.id,
            'estudiante_id': miembro.usuario.id,
            'nombre_estudiante': f"{miembro.usuario.nombre} {miembro.usuario.apellido}".strip(),
            'fecha_ingreso': miembro.fecha_asignacion,
        }, status=status.HTTP_201_CREATED)


# DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/
# Retira un estudiante del equipo marcando la membresía como 'retirado' (soft-delete).
# No elimina el registro histórico, solo cambia su estado y libera el cupo.
class RetirarMiembroView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def delete(self, request, equipo_id, usuario_id):
        """
        Busca la membresía activa del estudiante en el equipo y la marca como 'retirado'.
        Si no existe una membresía activa, retorna 404 automáticamente.
        """
        miembro = get_object_or_404(
            MiembroEquipo,
            equipo_id=equipo_id,
            usuario_id=usuario_id,
            estado='activo',
        )
        miembro.estado = 'retirado'
        miembro.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# PATCH /api/equipos/<equipo_id>/miembros/<usuario_id>/rol/
# Permite al propio estudiante actualizar su rol interno y descripción de responsabilidades.
# Verifica que el usuario autenticado sea el dueño de la membresía (propio estudiante).
# Valida que no exista ya un Líder en el equipo (salvo que sea el mismo usuario reasignándose).
# Retorna 200 con la membresía actualizada o 400 si ya existe un Líder en el equipo.
class ActualizarRolView(generics.UpdateAPIView):
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
            return Response(
                {'detail': 'Solo puedes actualizar tu propio rol.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(miembro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
# Sin proyecto_id: retorna {disponibles, en_equipo} con estado de asignación en el curso.
# Con proyecto_id: retorna lista plana de estudiantes sin equipo en ese proyecto.
class EstudiantesCursoView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, curso_id):
        proyecto_id = request.query_params.get('proyecto_id')

        if proyecto_id:
            proyecto = get_object_or_404(Proyecto, pk=proyecto_id, id_curso_id=curso_id)
            ya_asignados = MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto,
                estado='activo',
            ).values_list('usuario_id', flat=True)
            estudiantes = Usuario.objects.filter(
                tipo_rol='estudiante',
                estado='activo',
            ).exclude(id__in=ya_asignados).order_by('nombre', 'apellido')
            return Response(UsuarioResumenSerializer(estudiantes, many=True).data)

        # Sin proyecto_id: todos los estudiantes con su estado en el curso
        membresías = MiembroEquipo.objects.filter(
            equipo__proyecto__id_curso_id=curso_id,
            estado='activo',
        ).select_related('usuario', 'equipo', 'equipo__proyecto')

        usuario_equipos = {}
        for m in membresías:
            uid = m.usuario_id
            if uid not in usuario_equipos:
                usuario_equipos[uid] = []
            usuario_equipos[uid].append({
                'equipo_id':       m.equipo.id,
                'equipo_nombre':   m.equipo.nombre,
                'proyecto_id':     m.equipo.proyecto.id,
                'proyecto_nombre': m.equipo.proyecto.nombre,
            })

        todos = Usuario.objects.filter(
            tipo_rol='estudiante',
            estado='activo',
        ).order_by('nombre', 'apellido')

        disponibles = []
        en_equipo = []

        for est in todos:
            data = {
                'id':               est.id,
                'nombre':           est.nombre,
                'apellido':         est.apellido,
                'correo':           est.correo,
                'codigo_estudiante': est.codigo_estudiante or '',
            }
            if est.id in usuario_equipos:
                data['equipos'] = usuario_equipos[est.id]
                en_equipo.append(data)
            else:
                disponibles.append(data)

        return Response({'disponibles': disponibles, 'en_equipo': en_equipo})


# Kept for backwards compatibility — use EstudiantesCursoView instead.
class EstudiantesDisponiblesView(generics.ListAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = UsuarioResumenSerializer

    def get_queryset(self):
        curso_id = self.kwargs['curso_id']
        proyecto_id = self.request.query_params.get('proyecto_id')

        if not proyecto_id:
            raise ValidationError("Se requiere el parámetro proyecto_id.")

        proyecto = get_object_or_404(Proyecto, pk=proyecto_id, id_curso_id=curso_id)

        ya_asignados = MiembroEquipo.objects.filter(
            equipo__proyecto=proyecto,
            estado='activo',
        ).values_list('usuario_id', flat=True)

        return Usuario.objects.filter(
            tipo_rol='estudiante',
            estado='activo',
        ).exclude(id__in=ya_asignados)
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
