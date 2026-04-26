from django.core.exceptions import ObjectDoesNotExist

from rest_framework import generics, status
from rest_framework.response import Response

from apps.configuracion.models import PeriodoAcademico
from .models import Curso
from .permissions import EsDocente
from .serializers import CursoSerializer, CursoUpdateSerializer


class CursoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/cursos/ — Lista los cursos del docente autenticado en el período activo.
    POST /api/cursos/ — Crea un curso nuevo (docente queda como propietario).

    Respuestas GET:
      200  Lista de cursos (puede ser vacía).
      403  El usuario no tiene rol de docente.

    Respuestas POST:
      201  Curso creado con éxito.
      400  Errores de validación.
      403  El usuario no tiene rol de docente.
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
            .prefetch_related('proyecto__equipos')
            .order_by('-fecha_creacion')
        )


class CursoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/cursos/:id/ — Detalle de un curso del docente.
    PUT    /api/cursos/:id/ — Actualiza nombre, descripción y estado.
    PATCH  /api/cursos/:id/ — Actualización parcial de nombre, descripción y estado.
    DELETE /api/cursos/:id/ — Elimina el curso si no tiene proyectos vinculados.

    Respuestas PUT/PATCH:
      200  Curso actualizado (retorna representación completa).
      400  Errores de validación.
      403  El usuario no tiene rol de docente o no es el propietario.
      404  El curso no existe o no pertenece al docente autenticado.

    Respuestas DELETE:
      204  Curso eliminado.
      404  El curso no existe o no pertenece al docente autenticado.
      409  El curso tiene proyectos vinculados; no se puede eliminar.
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Curso.objects
            .filter(id_docente=self.request.user)
            .select_related('id_docente', 'id_periodo_academico')
            .prefetch_related('proyecto__equipos')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CursoUpdateSerializer
        return CursoSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            _ = instance.proyecto
            return Response(
                {'detail': 'No se puede eliminar el curso porque tiene proyectos vinculados.'},
                status=status.HTTP_409_CONFLICT,
            )
        except ObjectDoesNotExist:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)