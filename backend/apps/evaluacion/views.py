from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cursos.models import Proyecto
from apps.cursos.permissions import EsDocente, EsDocenteOAdministrador
from apps.entregables.models import Entregable
from apps.equipos.models import Equipo, MiembroEquipo
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from .models import Autoevaluacion, Coevaluacion, Evaluacion, Retroalimentacion, Rubrica
from .serializers import (
    AutoevaluacionCreateSerializer,
    AutoevaluacionSerializer,
    CoevaluacionCreateSerializer,
    CoevaluacionSerializer,
    EvaluacionCreateSerializer,
    EvaluacionPublicarSerializer,
    EvaluacionSerializer,
    RetroalimentacionCreateSerializer,
    RetroalimentacionSerializer,
    RubricaCreateSerializer,
    RubricaSerializer,
    RubricaUpdateSerializer,
)


# ---------------------------------------------------------------------------
# HU-23: Rúbricas
# ---------------------------------------------------------------------------

class RubricaListCreateView(generics.ListCreateAPIView):
    """
    GET  — docente: sus rúbricas; admin: todas.
    POST — docente únicamente: crea rúbrica completa (criterios + niveles) en una sola llamada.
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [EsDocenteOAdministrador()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RubricaCreateSerializer
        return RubricaSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            Rubrica.objects
            .select_related('id_proyecto', 'id_docente')
            .prefetch_related('criterios__niveles', 'criterios__id_rap')
            .order_by('-fecha_creacion')
        )
        if getattr(user, 'tipo_rol', None) == 'docente':
            qs = qs.filter(id_docente=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(id_docente=self.request.user)


class RubricaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — detalle de la rúbrica con criterios y niveles.
    PATCH  — actualiza campos escalares de la rúbrica (no criterios).
    DELETE — elimina la rúbrica y sus criterios/niveles en cascada.

    El docente solo puede acceder a sus propias rúbricas.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocenteOAdministrador]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return RubricaUpdateSerializer
        return RubricaSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            Rubrica.objects
            .select_related('id_proyecto', 'id_docente')
            .prefetch_related('criterios__niveles', 'criterios__id_rap')
        )
        if getattr(user, 'tipo_rol', None) == 'docente':
            qs = qs.filter(id_docente=user)
        return qs


# ---------------------------------------------------------------------------
# HU-24: Evaluaciones de entregables
# ---------------------------------------------------------------------------

def _get_entregable_con_acceso(pk, user):
    """
    Devuelve el entregable si el usuario tiene acceso:
    - Docente: debe ser el docente del curso del proyecto.
    - Estudiante/líder: debe ser miembro activo del equipo del entregable.
    Lanza PermissionDenied si no tiene acceso.
    """
    from apps.equipos.models import MiembroEquipo

    entregable = get_object_or_404(
        Entregable.objects.select_related(
            'id_actividad__id_fase__id_proyecto__id_curso__id_docente',
            'id_equipo',
        ),
        pk=pk,
    )
    proyecto = entregable.id_actividad.id_fase.id_proyecto
    tipo_rol = getattr(user, 'tipo_rol', None)

    if tipo_rol == 'docente':
        if proyecto.id_curso.id_docente_id != user.pk:
            raise PermissionDenied('No eres el docente de este proyecto.')
    else:
        es_miembro = MiembroEquipo.objects.filter(
            usuario=user,
            equipo=entregable.id_equipo,
            estado='activo',
        ).exists()
        if not es_miembro:
            raise PermissionDenied('No perteneces al equipo que realizó este entregable.')

    return entregable


class EvaluacionListCreateView(APIView):
    """
    GET  /api/entregables/<id_entregable>/evaluaciones/
         Docente: ve todas (borrador + publicadas).
         Equipo:  solo ve las publicadas.

    POST /api/entregables/<id_entregable>/evaluaciones/
         Solo docente. Crea una evaluación seleccionando el nivel
         de desempeño de cada criterio. La puntuación total se calcula
         automáticamente.
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def get(self, request, id_entregable):
        entregable = _get_entregable_con_acceso(id_entregable, request.user)
        tipo_rol = getattr(request.user, 'tipo_rol', None)

        qs = (
            Evaluacion.objects
            .filter(id_entregable=entregable)
            .select_related('id_rubrica', 'id_docente')
            .prefetch_related(
                'calificaciones__id_criterio',
                'calificaciones__id_nivel_seleccionado',
            )
            .order_by('-fecha_evaluacion')
        )

        # El equipo/estudiante solo ve evaluaciones publicadas
        if tipo_rol not in ('docente', 'administrador'):
            qs = qs.filter(estado=Evaluacion.Estado.PUBLICADA)

        serializer = EvaluacionSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, id_entregable):
        entregable = _get_entregable_con_acceso(id_entregable, request.user)

        serializer = EvaluacionCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        evaluacion = serializer.save(
            id_entregable=entregable,
            id_docente=request.user,
        )
        # Reload with related data for the response
        evaluacion = (
            Evaluacion.objects
            .select_related('id_rubrica', 'id_docente')
            .prefetch_related(
                'calificaciones__id_criterio',
                'calificaciones__id_nivel_seleccionado',
            )
            .get(pk=evaluacion.pk)
        )
        return Response(
            EvaluacionSerializer(evaluacion, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class EvaluacionPublicarView(APIView):
    """
    PATCH /api/evaluaciones/<pk>/publicar/

    Cambia el estado de una evaluación de 'borrador' a 'publicada',
    haciendo visible la calificación para el equipo evaluado.
    Solo el docente que creó la evaluación puede publicarla.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def patch(self, request, pk):
        evaluacion = get_object_or_404(
            Evaluacion.objects
            .select_related('id_rubrica', 'id_docente')
            .prefetch_related(
                'calificaciones__id_criterio',
                'calificaciones__id_nivel_seleccionado',
            ),
            pk=pk,
        )

        if evaluacion.id_docente_id != request.user.pk:
            raise PermissionDenied('Solo el docente que creó la evaluación puede publicarla.')

        if evaluacion.estado == Evaluacion.Estado.PUBLICADA:
            return Response(
                {'detail': 'La evaluación ya está publicada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EvaluacionPublicarSerializer(
            evaluacion,
            data={},
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# HU-25: Retroalimentación
# ---------------------------------------------------------------------------

def _get_proyecto_con_acceso_docente(pk, user):
    """Devuelve el proyecto si el usuario es su docente, o lanza PermissionDenied."""
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if proyecto.id_curso.id_docente_id != user.pk:
        raise PermissionDenied("No eres el docente de este proyecto.")
    return proyecto


class RetroalimentacionCreateView(APIView):
    """
    POST /api/proyectos/<id_proyecto>/retroalimentaciones/

    El docente registra retroalimentación libre vinculada a un equipo,
    un estudiante individual o una actividad del proyecto.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def post(self, request, id_proyecto):
        proyecto = _get_proyecto_con_acceso_docente(id_proyecto, request.user)

        serializer = RetroalimentacionCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        retro = serializer.save(
            id_proyecto=proyecto,
            id_docente=request.user,
        )
        retro = (
            Retroalimentacion.objects
            .select_related('id_docente', 'id_equipo', 'id_estudiante', 'id_actividad')
            .get(pk=retro.pk)
        )
        return Response(
            RetroalimentacionSerializer(retro, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class RetroalimentacionEquipoView(APIView):
    """
    GET /api/equipos/<id_equipo>/retroalimentaciones/

    Retorna las retroalimentaciones recibidas por el equipo (grupal)
    y por sus miembros individuales (individual), ordenadas por fecha descendente.

    Acceso: el docente del proyecto, los miembros activos del equipo o admin/director.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id_equipo):
        equipo = get_object_or_404(
            Equipo.objects.select_related('proyecto__id_curso__id_docente'),
            pk=id_equipo,
        )
        user = request.user
        tipo_rol = getattr(user, 'tipo_rol', None)
        proyecto = equipo.proyecto

        # Control de acceso
        if tipo_rol == 'docente':
            if proyecto.id_curso.id_docente_id != user.pk:
                raise PermissionDenied("No eres el docente de este equipo.")
        elif tipo_rol not in ('administrador', 'director'):
            es_miembro = MiembroEquipo.objects.filter(
                equipo=equipo, usuario=user, estado='activo'
            ).exists()
            if not es_miembro:
                raise PermissionDenied("No perteneces a este equipo.")

        miembro_ids = MiembroEquipo.objects.filter(
            equipo=equipo
        ).values_list('usuario_id', flat=True)

        qs = (
            Retroalimentacion.objects
            .filter(
                Q(id_equipo=equipo) |
                Q(id_estudiante__in=miembro_ids)
            )
            .select_related('id_docente', 'id_equipo', 'id_estudiante', 'id_actividad')
            .order_by('-fecha_registro')
        )
        return Response(RetroalimentacionSerializer(qs, many=True, context={'request': request}).data)


class RetroalimentacionEstudianteView(APIView):
    """
    GET /api/usuarios/<id_usuario>/retroalimentaciones/

    Retorna retroalimentaciones individuales recibidas por el estudiante.

    Acceso: el propio estudiante, cualquier docente o director/administrador.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id_usuario):
        estudiante = get_object_or_404(Usuario, pk=id_usuario)
        user = request.user
        tipo_rol = getattr(user, 'tipo_rol', None)

        # Solo el propio estudiante, docentes, director o admin
        puede_ver = (
            user.pk == id_usuario or
            tipo_rol in ('docente', 'director', 'administrador')
        )
        if not puede_ver:
            raise PermissionDenied(
                "Solo puedes consultar tus propias retroalimentaciones."
            )

        qs = (
            Retroalimentacion.objects
            .filter(id_estudiante=estudiante, tipo=Retroalimentacion.Tipo.INDIVIDUAL)
            .select_related('id_docente', 'id_equipo', 'id_estudiante', 'id_actividad')
            .order_by('-fecha_registro')
        )
        return Response(RetroalimentacionSerializer(qs, many=True, context={'request': request}).data)



# ---------------------------------------------------------------------------
# HU-26: Autoevaluacion
# ---------------------------------------------------------------------------

class AutoevaluacionListCreateView(APIView):
    """
    GET  /api/proyectos/<id_proyecto>/autoevaluaciones/
         Estudiante/lider: sus propias autoevaluaciones del proyecto.
         Docente/admin:    todas las autoevaluaciones del proyecto.

    POST /api/proyectos/<id_proyecto>/autoevaluaciones/
         Solo estudiante/lider de equipo: crea una autoevaluacion
         seleccionando un nivel por criterio de la rubrica elegida.
         La puntuacion_total se calcula automaticamente.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_proyecto(self, id_proyecto, user):
        proyecto = get_object_or_404(
            Proyecto.objects.select_related("id_curso__id_docente"),
            pk=id_proyecto,
        )
        tipo_rol = getattr(user, "tipo_rol", None)
        if tipo_rol == "docente":
            if proyecto.id_curso.id_docente_id != user.pk:
                raise PermissionDenied("No eres el docente de este proyecto.")
        elif tipo_rol in ("administrador", "director"):
            pass  # acceso total
        else:
            # Estudiante o lider: debe pertenecer al proyecto via equipo
            from apps.equipos.models import MiembroEquipo
            es_miembro = MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto,
                usuario=user,
                estado="activo",
            ).exists()
            if not es_miembro:
                raise PermissionDenied("No perteneces a este proyecto.")
        return proyecto

    def get(self, request, id_proyecto):
        proyecto = self._get_proyecto(id_proyecto, request.user)
        tipo_rol = getattr(request.user, "tipo_rol", None)

        qs = (
            Autoevaluacion.objects
            .filter(id_proyecto=proyecto)
            .select_related("id_estudiante", "id_rubrica")
            .prefetch_related("detalles__id_criterio", "detalles__id_nivel_seleccionado")
            .order_by("-fecha_registro")
        )

        # Estudiante/lider solo ve sus propias autoevaluaciones
        if tipo_rol not in ("docente", "administrador", "director"):
            qs = qs.filter(id_estudiante=request.user)

        return Response(AutoevaluacionSerializer(qs, many=True, context={"request": request}).data)

    def post(self, request, id_proyecto):
        tipo_rol = getattr(request.user, "tipo_rol", None)
        if tipo_rol not in ("estudiante", "lider_equipo"):
            raise PermissionDenied("Solo estudiantes y lideres de equipo pueden autoevaluarse.")

        proyecto = self._get_proyecto(id_proyecto, request.user)

        serializer = AutoevaluacionCreateSerializer(
            data=request.data,
            context={"request": request, "proyecto": proyecto},
        )
        serializer.is_valid(raise_exception=True)
        autoevaluacion = serializer.save()

        # Reload with related data for the response
        autoevaluacion = (
            Autoevaluacion.objects
            .select_related("id_estudiante", "id_rubrica")
            .prefetch_related("detalles__id_criterio", "detalles__id_nivel_seleccionado")
            .get(pk=autoevaluacion.pk)
        )
        return Response(
            AutoevaluacionSerializer(autoevaluacion, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# HU-27: Coevaluación
# ---------------------------------------------------------------------------

class CoevaluacionListCreateView(APIView):
    """
    GET  /api/proyectos/<id_proyecto>/coevaluaciones/
         Estudiante/lider: coevaluaciones donde participa como evaluador o evaluado.
         Docente/admin/director: todas las del proyecto.

    POST /api/proyectos/<id_proyecto>/coevaluaciones/
         Solo estudiante/lider: coevalúa a un compañero del mismo equipo.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_proyecto(self, id_proyecto, user):
        proyecto = get_object_or_404(
            Proyecto.objects.select_related("id_curso__id_docente"),
            pk=id_proyecto,
        )
        tipo_rol = getattr(user, "tipo_rol", None)
        if tipo_rol == "docente":
            if proyecto.id_curso.id_docente_id != user.pk:
                raise PermissionDenied("No eres el docente de este proyecto.")
        elif tipo_rol in ("administrador", "director"):
            pass
        else:
            es_miembro = MiembroEquipo.objects.filter(
                equipo__proyecto=proyecto,
                usuario=user,
                estado="activo",
            ).exists()
            if not es_miembro:
                raise PermissionDenied("No perteneces a este proyecto.")
        return proyecto

    def get(self, request, id_proyecto):
        proyecto = self._get_proyecto(id_proyecto, request.user)
        tipo_rol = getattr(request.user, "tipo_rol", None)

        qs = (
            Coevaluacion.objects
            .filter(id_proyecto=proyecto)
            .select_related("id_evaluador", "id_evaluado", "id_rubrica")
            .prefetch_related("detalles__id_criterio", "detalles__id_nivel_seleccionado")
            .order_by("-fecha_registro")
        )

        if tipo_rol not in ("docente", "administrador", "director"):
            from django.db.models import Q as DQ
            qs = qs.filter(
                DQ(id_evaluador=request.user) | DQ(id_evaluado=request.user)
            )

        return Response(CoevaluacionSerializer(qs, many=True, context={"request": request}).data)

    def post(self, request, id_proyecto):
        tipo_rol = getattr(request.user, "tipo_rol", None)
        if tipo_rol not in ("estudiante", "lider_equipo"):
            raise PermissionDenied("Solo estudiantes y líderes de equipo pueden coevaluar.")

        proyecto = self._get_proyecto(id_proyecto, request.user)

        serializer = CoevaluacionCreateSerializer(
            data=request.data,
            context={"request": request, "proyecto": proyecto},
        )
        serializer.is_valid(raise_exception=True)
        coevaluacion = serializer.save()

        coevaluacion = (
            Coevaluacion.objects
            .select_related("id_evaluador", "id_evaluado", "id_rubrica")
            .prefetch_related("detalles__id_criterio", "detalles__id_nivel_seleccionado")
            .get(pk=coevaluacion.pk)
        )
        return Response(
            CoevaluacionSerializer(coevaluacion, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
