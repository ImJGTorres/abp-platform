from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.configuracion.models import PeriodoAcademico
from apps.equipos.models import MiembroEquipo
from .models import Curso, Proyecto
from .permissions import EsDocente
from .serializers import (
    CursoSerializer,
    CursoUpdateSerializer,
    ProyectoCreateSerializer,
    ProyectoSerializer,
    ProyectoUpdateSerializer,
)


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------

class CursoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/cursos/ — Lista cursos del docente autenticado en el período activo.
    POST /api/cursos/ — Crea un curso (docente queda como propietario).
    """

    serializer_class = CursoSerializer
    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Curso.objects
            .filter(
                id_docente=self.request.user,
                id_periodo_academico__estado=PeriodoAcademico.Estado.ACTIVO,
            )
            .select_related('id_docente', 'id_periodo_academico')
            .prefetch_related('proyectos__equipos')
            .order_by('-fecha_creacion')
        )


class CursoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/cursos/:id/ — Detalle de un curso propio.
    PUT    /api/cursos/:id/ — Actualiza nombre, descripción y estado.
    DELETE /api/cursos/:id/ — Elimina si no tiene proyectos vinculados (409 si los tiene).
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Curso.objects
            .filter(id_docente=self.request.user)
            .select_related('id_docente', 'id_periodo_academico')
            .prefetch_related('proyectos__equipos')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CursoUpdateSerializer
        return CursoSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.proyectos.exists():
            return Response(
                {'detail': 'No se puede eliminar el curso porque tiene proyectos vinculados.'},
                status=status.HTTP_409_CONFLICT,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Proyectos
# ---------------------------------------------------------------------------

class ProyectoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/cursos/:curso_id/proyectos/ — Lista proyectos del curso ordenados por fecha_inicio.
         Accesible para el docente propietario y para estudiantes activos del curso.
    POST /api/cursos/:curso_id/proyectos/ — Crea un proyecto (solo el docente propietario).
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProyectoCreateSerializer
        return ProyectoSerializer

    def _get_curso(self):
        return get_object_or_404(Curso, pk=self.kwargs['curso_id'])

    def _check_acceso_curso(self, curso):
        """Verifica que el usuario tiene acceso a los proyectos del curso."""
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)

        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este curso.')
        elif tipo_rol == 'estudiante':
            tiene_equipo = MiembroEquipo.objects.filter(
                equipo__proyecto__id_curso=curso,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not tiene_equipo:
                raise PermissionDenied('No perteneces a ningún equipo de este curso.')
        else:
            raise PermissionDenied('Acceso no permitido.')

    def get_queryset(self):
        curso = self._get_curso()
        self._check_acceso_curso(curso)
        return (
            Proyecto.objects
            .filter(id_curso=curso)
            .prefetch_related('equipos')
            .order_by('fecha_inicio')
        )

    def perform_create(self, serializer):
        curso = self._get_curso()
        if curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este curso.')
        serializer.save(id_curso=curso)


class ProyectoDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/proyectos/:id/ — Detalle del proyecto.
    PUT   /api/proyectos/:id/ — Actualiza nombre, descripción, estado y fechas.
    PATCH /api/proyectos/:id/ — Actualización parcial.

    Solo el docente propietario del curso al que pertenece el proyecto puede modificarlo.
    La vista filtra por docente en el queryset: un proyecto ajeno devuelve 404.
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Proyecto.objects
            .filter(id_curso__id_docente=self.request.user)
            .select_related('id_curso')
            .prefetch_related('equipos')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProyectoUpdateSerializer
        return ProyectoSerializer