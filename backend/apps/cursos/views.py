<<<<<<< HEAD
import io

=======
from django.core.exceptions import ObjectDoesNotExist
>>>>>>> feature/HU-011-frontend
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.configuracion.models import PeriodoAcademico
<<<<<<< HEAD
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer
=======
from .models import Curso, Proyecto
from .permissions import EsDocente
from .serializers import CursoSerializer, CursoUpdateSerializer, ProyectoSerializer
>>>>>>> feature/HU-011-frontend

from .models import Curso, Proyecto
from .permissions import EsAdministrador, EsDocente, EsDocenteOAdministrador
from .serializers import (
    CursoAdminCreateSerializer,
    CursoAdminUpdateSerializer,
    CursoSerializer,
    CursoUpdateSerializer,
    ProyectoSerializer,
)


# ── Cursos ────────────────────────────────────────────────────────────────────

class CursoListCreateView(generics.ListCreateAPIView):
    """
    GET  — docente: sus cursos; admin: todos los cursos.
    POST — admin únicamente: crea un curso asignando docente.
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsAdministrador()]
        return [EsDocenteOAdministrador()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CursoAdminCreateSerializer
        return CursoSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            Curso.objects
            .select_related('id_docente', 'id_periodo_academico')
<<<<<<< HEAD
=======
            .prefetch_related('proyectos__equipos')
>>>>>>> feature/HU-011-frontend
            .order_by('-fecha_creacion')
        )
        if getattr(user, 'tipo_rol', None) == 'docente':
            qs = qs.filter(id_docente=user)
        return qs

    def perform_create(self, serializer):
        curso = serializer.save()
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='cursos',
            descripcion=f'Curso creado: ID={curso.id}, codigo={curso.codigo}',
        )


class CursoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    — docente: su curso; admin: cualquier curso.
    PATCH  — docente: nombre/descripcion/estado; admin: todos los campos.
    DELETE — admin únicamente.
    """

<<<<<<< HEAD
    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [EsAdministrador()]
        return [EsDocenteOAdministrador()]
=======
    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Curso.objects
            .filter(id_docente=self.request.user)
            .select_related('id_docente', 'id_periodo_academico')
            .prefetch_related('proyectos__equipos')
        )
>>>>>>> feature/HU-011-frontend

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            user = self.request.user
            if getattr(user, 'tipo_rol', None) == 'administrador':
                return CursoAdminUpdateSerializer
            return CursoUpdateSerializer
        return CursoSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            Curso.objects
            .select_related('id_docente', 'id_periodo_academico')
        )
        if getattr(user, 'tipo_rol', None) == 'docente':
            qs = qs.filter(id_docente=user)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.proyectos.exists():
            return Response(
                {'detail': 'No se puede eliminar el curso porque tiene proyectos vinculados.'},
                status=status.HTTP_409_CONFLICT,
            )
<<<<<<< HEAD
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='cursos',
            descripcion=f'Curso eliminado: ID={instance.id}, codigo={instance.codigo}',
        )
=======
>>>>>>> feature/HU-011-frontend
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


<<<<<<< HEAD
# ── Proyectos anidados bajo curso ─────────────────────────────────────────────

class ProyectoListCreateView(generics.ListCreateAPIView):
    """
    GET  — docente (propio curso) o admin: lista proyectos del curso.
    POST — docente únicamente: crea un proyecto en su curso.
    """
    serializer_class = ProyectoSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [EsDocenteOAdministrador()]

    def _get_curso(self):
        user = self.request.user
        qs = Curso.objects.all()
        if getattr(user, 'tipo_rol', None) == 'docente':
            qs = qs.filter(id_docente=user)
        return get_object_or_404(qs, pk=self.kwargs['curso_pk'])

    def get_queryset(self):
        curso = self._get_curso()
        return Proyecto.objects.filter(id_curso=curso).prefetch_related('equipos').order_by('-fecha_creacion')

    def perform_create(self, serializer):
        curso = self._get_curso()
        proyecto = serializer.save(id_curso=curso)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='proyectos',
            descripcion=f'Proyecto creado: ID={proyecto.id}, nombre={proyecto.nombre}',
        )


class ProyectoDetailView(generics.RetrieveUpdateAPIView):
    """PATCH/PUT — docente: edita su proyecto."""
    serializer_class = ProyectoSerializer
    permission_classes = [EsDocente]

    def get_queryset(self):
        return Proyecto.objects.filter(
            id_curso__id=self.kwargs['curso_pk'],
            id_curso__id_docente=self.request.user,
        ).prefetch_related('equipos')


# ── Carga masiva de cursos (admin) ────────────────────────────────────────────

class CursoCargaMasivaView(APIView):
    """POST /api/cursos/carga-masiva/ — importa cursos desde Excel."""
    permission_classes = [EsAdministrador]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'detail': 'Se requiere un archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        if not archivo.name.endswith('.xlsx'):
            return Response({'detail': 'El archivo debe ser formato .xlsx.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(archivo.read()), data_only=True)
            ws = wb.active
        except Exception:
            return Response({'detail': 'No se pudo leer el archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        creados = 0
        omitidos = 0
        errores = []

        # Buscar período activo
        periodo_activo = PeriodoAcademico.objects.filter(estado=PeriodoAcademico.Estado.ACTIVO).first()
        if not periodo_activo:
            return Response({'detail': 'No hay un período académico activo.'}, status=status.HTTP_400_BAD_REQUEST)

        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue

            nombre = str(row[0]).strip() if row[0] else ''
            codigo = str(row[1]).strip().upper() if row[1] else ''
            descripcion = str(row[2]).strip() if len(row) > 2 and row[2] else ''
            correo_docente = str(row[3]).strip() if len(row) > 3 and row[3] else ''
            try:
                cantidad_max = int(row[4]) if len(row) > 4 and row[4] else 30
            except (ValueError, TypeError):
                cantidad_max = 30

            if not nombre or not codigo:
                errores.append({'fila': i, 'codigo': codigo or '—', 'motivo': 'nombre y código son obligatorios'})
                omitidos += 1
                continue

            # Buscar docente
            docente = None
            if correo_docente:
                docente = Usuario.objects.filter(correo=correo_docente, tipo_rol='docente').first()
                if not docente:
                    errores.append({'fila': i, 'codigo': codigo, 'motivo': f'docente no encontrado: {correo_docente}'})
                    omitidos += 1
                    continue

            if not docente:
                errores.append({'fila': i, 'codigo': codigo, 'motivo': 'correo del docente es obligatorio'})
                omitidos += 1
                continue

            # Verificar unicidad código+periodo
            if Curso.objects.filter(codigo=codigo, id_periodo_academico=periodo_activo).exists():
                errores.append({'fila': i, 'codigo': codigo, 'motivo': 'código ya existe en este período'})
                omitidos += 1
                continue

            Curso.objects.create(
                nombre=nombre,
                codigo=codigo,
                descripcion=descripcion,
                id_docente=docente,
                id_periodo_academico=periodo_activo,
                usuario_creo=request.user,
                cantidad_max_estudiantes=cantidad_max,
            )
            creados += 1

        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='cursos',
            descripcion=f'Carga masiva de cursos: {creados} creados, {omitidos} omitidos',
        )

        return Response({'creados': creados, 'omitidos': omitidos, 'errores': errores}, status=status.HTTP_200_OK)


# ── Listado de docentes (para selector en formulario admin) ───────────────────

class DocenteListView(generics.ListAPIView):
    """GET /api/cursos/docentes/ — lista usuarios con rol docente."""
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdministrador]

    def get_queryset(self):
        return Usuario.objects.filter(tipo_rol='docente', estado='activo').order_by('nombre')
=======
class ProyectoListCreateView(generics.ListCreateAPIView):
    """
    GET    /api/cursos/<curso_id>/proyectos/ — Lista todos los proyectos del curso.
    POST   /api/cursos/<curso_id>/proyectos/ — Crea un nuevo proyecto para el curso.
    """

    serializer_class = ProyectoSerializer
    permission_classes = [EsDocente]

    def get_curso(self):
        return get_object_or_404(
            Curso.objects.filter(id_docente=self.request.user),
            pk=self.kwargs.get('curso_id')
        )

    def get_queryset(self):
        curso = self.get_curso()
        return curso.proyectos.all().prefetch_related(
            'equipos__miembros__usuario'
        ).order_by('-fecha_creacion')

    def perform_create(self, serializer):
        curso = self.get_curso()
        serializer.save(id_curso=curso)


class ProyectoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/cursos/<curso_id>/proyectos/<proyecto_id>/ — Detalle de un proyecto.
    PUT    /api/cursos/<curso_id>/proyectos/<proyecto_id>/ — Actualiza el proyecto.
    PATCH  /api/cursos/<curso_id>/proyectos/<proyecto_id>/ — Actualización parcial.
    DELETE /api/cursos/<curso_id>/proyectos/<proyecto_id>/ — Elimina el proyecto.
    """

    serializer_class = ProyectoSerializer
    permission_classes = [EsDocente]

    def get_curso(self):
        return get_object_or_404(
            Curso.objects.filter(id_docente=self.request.user),
            pk=self.kwargs.get('curso_id')
        )

    def get_queryset(self):
        curso = self.get_curso()
        return curso.proyectos.all()
>>>>>>> feature/HU-011-frontend
