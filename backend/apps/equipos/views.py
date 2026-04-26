from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.cursos.models import Proyecto
from apps.usuarios.models import Usuario
from apps.bitacora.models import BitacoraSistema
from .models import Equipo, MiembroEquipo
from .serializers import (
    EquipoDetalleSerializer, EstudianteDisponibleSerializer,
    MiembroEquipoSerializer, UsuarioResumenSerializer,
)


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



# BE-03: GET /api/equipos/<equipo_id>/miembros/
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


# BE-04: DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/
class RetirarMiembroView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def delete(self, request, equipo_id, usuario_id):
        miembro = get_object_or_404(
            MiembroEquipo,
            equipo_id=equipo_id,
            usuario_id=usuario_id,
            estado='activo',
        )
        miembro.estado = 'retirado'
        miembro.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# BE-05: GET /api/cursos/<curso_id>/estudiantes/?proyecto_id=<int>
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