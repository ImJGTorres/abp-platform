import io
import logging

from django.db import connection, transaction
from django.db.models import Avg, Count, FloatField, OuterRef, Prefetch, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.configuracion.models import PeriodoAcademico
from apps.equipos.models import Equipo, MiembroEquipo
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer
from apps.usuarios.authentication import UsuarioJWTAuthentication
from .models import Actividad, AvanceActividad, Curso, CursoEstudiante, FaseProyecto, HitoProyecto, ObjetivoProyecto, Proyecto, ResultadoAprendizaje, VistaProgresoFase, VistaProgresoProyecto
from .permissions import EsAdministrador, EsDocente, EsDocenteOAdministrador, EsLiderEquipo
from .serializers import (
    ActividadAsignarResponsableSerializer,
    ActividadAsignarSerializer,
    ActividadCreateSerializer,
    ActividadPorEquipoSerializer,
    ActividadSerializer,
    ActividadUpdateSerializer,
    AvanceActividadCreateSerializer,
    AvanceActividadSerializer,
    CursoAdminCreateSerializer,
    CursoAdminUpdateSerializer,
    CursoSerializer,
    CursoUpdateSerializer,
    FaseCreateSerializer,
    FaseSerializer,
    FaseUpdateSerializer,
    HitoCreateSerializer,
    HitoSerializer,
    HitoUpdateSerializer,
    ObjetivoSerializer,
    ObjetivoUpdateSerializer,
    ProyectoCreateSerializer,
    ProyectoSerializer,
    ProyectoUpdateSerializer,
    RapCreateSerializer,
    RapSerializer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------

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
            .prefetch_related('proyectos__equipos')
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

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [EsAdministrador()]
        return [EsDocenteOAdministrador()]

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
            .prefetch_related('proyectos__equipos')
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
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='cursos',
            descripcion=f'Curso eliminado: ID={instance.id}, codigo={instance.codigo}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Proyectos
# ---------------------------------------------------------------------------

class ProyectoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/cursos/<curso_id>/proyectos/ — Lista proyectos del curso.
         Accesible para el docente propietario, admin y estudiantes activos del curso.
    POST /api/cursos/<curso_id>/proyectos/ — Crea un proyecto (solo el docente propietario).
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
        """Verifica que el usuario autenticado tenga acceso a los proyectos del curso.

        Reglas de negocio:
            - Administrador: acceso irrestricto.
            - Docente: solo si es el propietario del curso (id_docente).
            - Estudiante / lider_equipo: solo si pertenece activamente a algún
              equipo cuyo proyecto esté vinculado al curso.
            - Cualquier otro rol: acceso denegado.

        Args:
            curso: Instancia de Curso a verificar.

        Raises:
            PermissionDenied: Si el usuario no cumple ninguna de las reglas de acceso.
        """
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este curso.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
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
            .con_progreso()
            .prefetch_related('equipos')
            .order_by('fecha_inicio')
        )

    def perform_create(self, serializer):
        curso = self._get_curso()
        if curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este curso.')
        proyecto = serializer.save(id_curso=curso)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='proyectos',
            descripcion=f'Proyecto creado: ID={proyecto.id}, nombre={proyecto.nombre}',
        )


class ProyectoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/proyectos/<pk>/ — Detalle del proyecto.
                                  Docente: solo sus proyectos.
                                  Estudiante/líder: solo proyectos en los que es miembro activo.
    PUT    /api/proyectos/<pk>/ — Actualiza nombre, descripción, estado y fechas. Solo docente.
    PATCH  /api/proyectos/<pk>/ — Actualización parcial. Solo docente.
    DELETE /api/proyectos/<pk>/ — Elimina el proyecto (409 si tiene equipos vinculados). Solo docente.
    """

    authentication_classes = [UsuarioJWTAuthentication]

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsAuthenticated()]
        return [EsDocente()]

    def get_queryset(self):
        user = self.request.user
        tipo_rol = getattr(user, 'tipo_rol', None)
        qs = (
            Proyecto.objects
            .select_related('id_curso')
            .prefetch_related('equipos')
        )
        if tipo_rol == 'docente':
            return qs.filter(id_curso__id_docente=user)
        elif tipo_rol in ('estudiante', 'lider_equipo'):
            proyecto_ids = MiembroEquipo.objects.filter(
                usuario=user,
                estado='activo',
            ).values_list('equipo__proyecto_id', flat=True)
            return qs.filter(id__in=proyecto_ids)
        # admin / director: acceso total
        return qs

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProyectoUpdateSerializer
        return ProyectoSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='proyectos',
            descripcion=f'Proyecto eliminado: ID={instance.id}, nombre={instance.nombre}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.equipos.exists():
            return Response(
                {'detail': 'No se puede eliminar el proyecto porque tiene equipos vinculados.'},
                status=status.HTTP_409_CONFLICT,
            )
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='proyectos',
            descripcion=f'Proyecto eliminado: ID={instance.id}, nombre={instance.nombre}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Carga masiva de cursos (admin)
# ---------------------------------------------------------------------------

class CursoCargaMasivaView(APIView):
    """
    POST /api/cursos/carga-masiva/
    Importa cursos desde Excel con formato del cliente:
    columnas Materia (→ codigo), Nombre (→ nombre). Filas con Materia vacía se omiten
    (corresponden a horarios adicionales del mismo curso).
    El docente queda en NULL; el administrador lo asigna después.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsAdministrador]
    parser_classes = [MultiPartParser]

    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'detail': 'Se requiere un archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        if not archivo.name.lower().endswith('.xlsx'):
            return Response({'detail': 'El archivo debe ser formato .xlsx.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(archivo.read()), data_only=True)
            ws = wb.active
        except Exception:
            return Response({'detail': 'No se pudo leer el archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        periodo_activo = PeriodoAcademico.objects.filter(estado=PeriodoAcademico.Estado.ACTIVO).first()
        if not periodo_activo:
            return Response({'detail': 'No hay un período académico activo.'}, status=status.HTTP_400_BAD_REQUEST)

        creados = 0
        omitidos = 0
        errores = []

        # Columna 0 = Materia (código), columna 1 = Nombre; omitir filas donde col 0 es None
        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row) or row[0] is None:
                continue

            codigo = str(row[0]).strip().upper()
            nombre = str(row[1]).strip() if len(row) > 1 and row[1] else ''

            if not codigo or not nombre:
                errores.append({'fila': i, 'codigo': codigo or '—', 'motivo': 'código y nombre son obligatorios'})
                omitidos += 1
                continue

            if Curso.objects.filter(codigo=codigo, id_periodo_academico=periodo_activo).exists():
                omitidos += 1
                continue

            try:
                Curso.objects.create(
                    nombre=nombre,
                    codigo=codigo,
                    id_docente=None,
                    id_periodo_academico=periodo_activo,
                    usuario_creo=request.user,
                    cantidad_max_estudiantes=30,
                    estado=Curso.Estado.ACTIVO,
                )
                creados += 1
            except Exception as exc:
                errores.append({'fila': i, 'codigo': codigo, 'motivo': f'error al crear: {exc}'})
                omitidos += 1

        try:
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.CREATE,
                modulo='cursos',
                descripcion=f'Carga masiva de cursos: {creados} creados, {omitidos} omitidos',
            )
        except Exception:
            pass

        return Response({'creados': creados, 'omitidos': omitidos, 'errores': errores}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Matrícula masiva de estudiantes por Excel (admin)
# ---------------------------------------------------------------------------

class CursoMatriculaExcelView(APIView):
    """
    POST /api/cursos/<curso_id>/estudiantes/importar/
    Matricula estudiantes desde Excel con formato del cliente (Matriculados POR MATERIA).
    El archivo tiene una sección de encabezado del curso (filas 1-N) seguida de una sección
    de estudiantes que comienza con una fila de encabezados que incluye 'Código'.
    Busca esa fila de encabezados y lee los datos de estudiantes a partir de la siguiente.
    Permiso: administrador o docente propietario del curso.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocenteOAdministrador]
    parser_classes = [MultiPartParser]

    def post(self, request, curso_id):
        import unicodedata

        curso = get_object_or_404(Curso, pk=curso_id)

        tipo_rol = getattr(request.user, 'tipo_rol', None)
        if tipo_rol == 'docente' and curso.id_docente_id != request.user.pk:
            return Response(
                {'detail': 'No eres el docente de este curso.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'detail': 'Se requiere un archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        if not archivo.name.lower().endswith('.xlsx'):
            return Response({'detail': 'El archivo debe ser formato .xlsx.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(archivo.read()), data_only=True)
            ws = wb.active
        except Exception:
            return Response({'detail': 'No se pudo leer el archivo Excel.'}, status=status.HTTP_400_BAD_REQUEST)

        def _norm(s):
            if s is None:
                return ''
            s = str(s).strip().lower()
            return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii')

        # Buscar la fila de encabezados de estudiantes (la que tiene 'Código' en col 0)
        all_rows = list(ws.iter_rows(values_only=True))
        header_row_idx = None
        for idx, row in enumerate(all_rows):
            if row and _norm(row[0]) == 'codigo':
                header_row_idx = idx
                break

        if header_row_idx is None:
            return Response(
                {'detail': 'No se encontró la sección de estudiantes (fila con "Código") en el archivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_rows = all_rows[header_row_idx + 1:]

        matriculados = 0
        ya_matriculados = 0
        no_encontrados = []
        rol_incorrecto = []

        try:
            with transaction.atomic():
                for row in student_rows:
                    if not any(row):
                        continue

                    raw = row[0]
                    # openpyxl puede devolver números como float (1152001.0);
                    # se normaliza a string sin decimales.
                    if isinstance(raw, float):
                        codigo = str(int(raw))
                    elif raw is not None:
                        codigo = str(raw).strip()
                    else:
                        codigo = ''

                    if not codigo or codigo.lower() == 'none':
                        continue

                    # Buscar por código independientemente del rol para dar
                    # un error más útil al usuario.
                    try:
                        usuario = Usuario.objects.get(codigo=codigo)
                    except Usuario.DoesNotExist:
                        no_encontrados.append(codigo)
                        continue

                    if usuario.tipo_rol != 'estudiante':
                        rol_incorrecto.append(codigo)
                        continue

                    if CursoEstudiante.objects.filter(curso=curso, estudiante=usuario).exists():
                        ya_matriculados += 1
                        continue

                    CursoEstudiante.objects.create(curso=curso, estudiante=usuario, estado='activo')
                    matriculados += 1

        except Exception as e:
            return Response({'detail': f'Error procesando el archivo: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.CREATE,
                modulo='cursos',
                descripcion=(
                    f'Matrícula masiva en curso ID={curso_id}: '
                    f'{matriculados} inscritos, {ya_matriculados} ya inscritos'
                ),
            )
        except Exception:
            pass

        return Response({
            'matriculados': matriculados,
            'ya_matriculados': ya_matriculados,
            'no_encontrados': no_encontrados,
            'rol_incorrecto': rol_incorrecto,
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Listado de docentes (para selector en formulario admin)
# ---------------------------------------------------------------------------

class DocenteListView(generics.ListAPIView):
    """GET /api/cursos/docentes/ — lista usuarios con rol docente."""
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdministrador]

    def get_queryset(self):
        return Usuario.objects.filter(tipo_rol='docente', estado='activo').order_by('nombre')


# ---------------------------------------------------------------------------
# Objetivos
# ---------------------------------------------------------------------------

def _reordenar_tras_borrado(proyecto, orden_borrado):
    """
    Decrementa en 1 el campo `orden` de todos los objetivos del proyecto
    cuyo orden sea mayor al del objetivo recién eliminado.

    Esto mantiene la secuencia de órdenes contigua (sin huecos) después
    de un borrado.

    Se itera en orden ascendente para respetar el constraint
    unique_orden_por_proyecto en bases de datos que validan la unicidad
    fila a fila (como SQLite). PostgreSQL tolera el UPDATE en batch sin
    problema, pero el loop es compatible con ambas.

    Ejemplo: órdenes [1, 2, 3, 4], se borra el 2.
      → itera 3→2, luego 4→3. Resultado: [1, 2, 3].
    """
    objetivos_afectados = (
        ObjetivoProyecto.objects
        .filter(id_proyecto=proyecto, orden__gt=orden_borrado)
        .order_by('orden')  # ascendente: actualiza primero el de orden menor
    )
    for obj in objetivos_afectados:
        obj.orden -= 1
        obj.save(update_fields=['orden'])  # una query por fila, seguro con el constraint


class ObjetivoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/proyectos/<proyecto_id>/objetivos/
         Lista los objetivos del proyecto ordenados por tipo y orden.
         Accesible para docente propietario, administrador y estudiantes
         activos en algún equipo del curso al que pertenece el proyecto.

    POST /api/proyectos/<proyecto_id>/objetivos/
         Crea uno o varios objetivos en un solo request.
         Solo el docente propietario del proyecto puede crearlos.

         Body objeto único:
           {"descripcion": "...", "tipo": "general", "orden": 1}

         Body lista (creación en lote):
           [
             {"descripcion": "...", "tipo": "general",    "orden": 1},
             {"descripcion": "...", "tipo": "especifico",  "orden": 2}
           ]

         Siempre retorna 201 con una lista de objetivos, incluso si el
         input fue un objeto individual.
    """

    # serializer_class por defecto para GET; POST lo sobreescribe via get_serializer_class.
    serializer_class = ObjetivoSerializer

    def get_permissions(self):
        # POST exige rol de docente; el control fino de propiedad está en perform_create.
        # GET es más permisivo: la verificación de acceso se hace en get_queryset.
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def _get_proyecto(self):
        """
        Obtiene el proyecto por PK desde la URL, con select_related para
        evitar una query adicional al acceder a id_curso.id_docente_id.
        """
        return get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=self.kwargs['proyecto_id'],
        )

    def _check_acceso_proyecto(self, proyecto):
        """
        Verifica que el usuario autenticado tenga derecho a ver los
        objetivos de este proyecto. Reglas por rol:

          - Administrador → acceso irrestricto.
          - Docente       → debe ser el propietario del curso del proyecto.
          - Estudiante    → debe tener al menos un equipo activo en el curso.
          - Otro rol      → denegado.
        """
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)

        if tipo_rol == 'administrador':
            return  # sin restricción adicional

        curso = proyecto.id_curso  # ya cargado via select_related

        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')

        elif tipo_rol in ('estudiante', 'lider_equipo'):
            # Comprueba membresía activa en CUALQUIER equipo del curso
            # (no solo del proyecto solicitado).
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
        """
        Devuelve los objetivos del proyecto.  La llamada a _check_acceso_proyecto
        dentro de este método garantiza que cualquier intento de GET sin acceso
        resulta en 403 antes de ejecutar la query a la BD.
        """
        proyecto = self._get_proyecto()
        self._check_acceso_proyecto(proyecto)
        # El ordenamiento por defecto está definido en Meta.ordering del modelo.
        return ObjetivoProyecto.objects.filter(id_proyecto=proyecto)

    def create(self, request, *args, **kwargs):
        """
        Acepta body como objeto individual o como lista de objetos.
        Detecta el tipo del body para activar many=True cuando corresponde.
        Siempre retorna 201 con lista para que el cliente tenga una interfaz
        uniforme independientemente de si creó uno o varios objetivos.
        """
        # isinstance(request.data, list) es True cuando el body es un array JSON.
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Normaliza la respuesta: siempre una lista.
        data = serializer.data if many else [serializer.data]
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """
        Inyecta id_proyecto desde la URL (el cliente no lo envía en el body)
        y verifica que el docente sea el propietario de este proyecto específico.
        """
        proyecto = self._get_proyecto()
        # get_permissions() ya garantiza tipo_rol=='docente'; aquí verificamos
        # que sea el propietario de ESTE proyecto, no de cualquiera.
        if proyecto.id_curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')
        # id_proyecto se pasa a save(); bulk_create lo aplica a todos los items.
        serializer.save(id_proyecto=proyecto)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='objetivos',
            descripcion=f'Objetivos creados para proyecto ID={proyecto.id}',
        )


class ObjetivoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/objetivos/<pk>/ — Detalle del objetivo.
    PUT    /api/objetivos/<pk>/ — Actualiza descripción, tipo y orden.
    PATCH  /api/objetivos/<pk>/ — Actualización parcial de los mismos campos.
    DELETE /api/objetivos/<pk>/ — Elimina y reordena los objetivos restantes.

    Solo el docente propietario del curso del proyecto puede acceder.
    El queryset filtra transitivamente por propietario (objetivo → proyecto
    → curso → docente), así que un objetivo ajeno devuelve 404.
    """

    # Todos los métodos requieren rol de docente.
    permission_classes = [EsDocente]

    def get_queryset(self):
        """
        Filtra por la cadena: objetivo.id_proyecto.id_curso.id_docente == usuario.
        select_related carga proyecto e id_curso en la misma query para evitar
        queries adicionales en destroy() y validate().
        """
        return (
            ObjetivoProyecto.objects
            .filter(id_proyecto__id_curso__id_docente=self.request.user)
            .select_related('id_proyecto__id_curso')
        )

    def get_serializer_class(self):
        # Para escritura usa el serializer restringido; para lectura el completo.
        if self.request.method in ('PUT', 'PATCH'):
            return ObjetivoUpdateSerializer
        return ObjetivoSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Elimina el objetivo y reordena los restantes del mismo proyecto
        para que la secuencia de 'orden' quede sin huecos.

        Ejemplo: proyecto con órdenes [1, 2, 3, 4].
          DELETE sobre orden=2  →  result: [1, 2, 3]
          (el antiguo 3 pasa a 2, el antiguo 4 pasa a 3).
        """
        instance = self.get_object()
        # Guardamos referencias antes de borrar porque delete() limpia el objeto.
        proyecto = instance.id_proyecto
        orden_borrado = instance.orden

        self.perform_destroy(instance)

        # Reordena los objetivos que quedaron por encima del borrado.
        _reordenar_tras_borrado(proyecto, orden_borrado)

        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='objetivos',
            descripcion=(
                f'Objetivo ID={instance.id} (orden={orden_borrado}) '
                f'eliminado del proyecto ID={proyecto.id}'
            ),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Hitos del cronograma
# ---------------------------------------------------------------------------

class HitoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/proyectos/<proyecto_id>/hitos/ — Lista hitos ordenados cronológicamente.
         Accesible para todos los participantes del curso (docente, admin, estudiantes activos).
    POST /api/proyectos/<proyecto_id>/hitos/ — Crea un hito (solo el docente propietario).
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HitoCreateSerializer
        return HitoSerializer

    def _get_proyecto(self):
        return get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=self.kwargs['proyecto_id'],
        )

    def _check_acceso_proyecto(self, proyecto):
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
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
        proyecto = self._get_proyecto()
        self._check_acceso_proyecto(proyecto)
        return HitoProyecto.objects.filter(id_proyecto=proyecto)

    def perform_create(self, serializer):
        proyecto = self._get_proyecto()
        if proyecto.id_curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')
        hito = serializer.save(id_proyecto=proyecto)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='hitos',
            descripcion=f'Hito creado: ID={hito.id}, nombre={hito.nombre}, proyecto ID={proyecto.id}',
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['proyecto'] = self._get_proyecto()
        return context


class HitoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/hitos/<pk>/ — Detalle del hito.
    PUT    /api/hitos/<pk>/ — Actualiza nombre, fechas y estado.
    PATCH  /api/hitos/<pk>/ — Actualización parcial.
    DELETE /api/hitos/<pk>/ — Elimina el hito (409 si tiene dependencias).

    Solo el docente propietario del curso del proyecto puede modificar o eliminar.
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            HitoProyecto.objects
            .filter(id_proyecto__id_curso__id_docente=self.request.user)
            .select_related('id_proyecto__id_curso')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return HitoUpdateSerializer
        return HitoSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='hitos',
            descripcion=f'Hito eliminado: ID={instance.id}, nombre={instance.nombre}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Estudiantes del curso (CursoEstudiante)
# ---------------------------------------------------------------------------

class CursoEstudianteView(APIView):
    """
    GET  /api/cursos/<curso_id>/estudiantes/ — lista estudiantes inscritos con su estado.
    POST /api/cursos/<curso_id>/estudiantes/ — inscribe un estudiante al curso.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocenteOAdministrador]

    def _get_curso(self, curso_id):
        return get_object_or_404(Curso, pk=curso_id)

    def get(self, request, curso_id):
        curso = self._get_curso(curso_id)

        inscripciones = (
            CursoEstudiante.objects
            .filter(curso=curso, estado='activo')
            .select_related('estudiante')
        )

        # Estudiantes con equipo activo en algún proyecto de este curso
        from apps.equipos.models import MiembroEquipo as _MiembroEquipo
        membresias = (
            _MiembroEquipo.objects
            .filter(equipo__proyecto__id_curso=curso, estado='activo')
            .select_related('usuario', 'equipo__proyecto')
        )
        en_proyecto = {}
        for m in membresias:
            uid = m.usuario_id
            if uid not in en_proyecto:
                en_proyecto[uid] = {'id': m.equipo.proyecto.id, 'nombre': m.equipo.proyecto.nombre}

        result = []
        for ins in inscripciones:
            est = ins.estudiante
            proyecto_data = en_proyecto.get(est.id)
            result.append({
                'id': est.id,
                'nombre': est.nombre,
                'apellido': est.apellido,
                'correo': est.correo,
                'codigo': getattr(est, 'codigo', '') or '',
                'estado_en_curso': 'en_proyecto' if proyecto_data else 'disponible',
                'proyecto': proyecto_data,
            })

        return Response(result)

    def post(self, request, curso_id):
        curso = self._get_curso(curso_id)
        estudiante_id = request.data.get('estudiante_id')
        if not estudiante_id:
            return Response({'detail': 'Se requiere estudiante_id.'}, status=status.HTTP_400_BAD_REQUEST)

        estudiante = get_object_or_404(Usuario, pk=estudiante_id, tipo_rol='estudiante')

        try:
            with transaction.atomic():
                inscripcion, creado = CursoEstudiante.objects.get_or_create(
                    curso=curso,
                    estudiante=estudiante,
                    defaults={'estado': 'activo'},
                )
                if not creado and inscripcion.estado != 'activo':
                    inscripcion.estado = 'activo'
                    inscripcion.save(update_fields=['estado'])
        except Exception:
            return Response(
                {'detail': 'No se pudo inscribir al estudiante.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.CREATE,
                modulo='cursos',
                descripcion=f'Estudiante ID={estudiante.id} inscrito en curso ID={curso.id}',
            )
        except Exception:
            pass

        return Response(
            {'detail': 'Estudiante inscrito correctamente.'},
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# RAPs (Resultados de Aprendizaje)
# ---------------------------------------------------------------------------

class RapListCreateView(APIView):
    """
    GET  /api/proyectos/<id_proyecto>/raps/ — lista RAPs del proyecto (usuario autenticado).
    POST /api/proyectos/<id_proyecto>/raps/ — crea RAP (solo docente propietario).
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def _get_proyecto(self, id_proyecto):
        return get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=id_proyecto,
        )

    def get(self, request, id_proyecto):
        proyecto = self._get_proyecto(id_proyecto)
        raps = ResultadoAprendizaje.objects.filter(proyecto=proyecto)
        return Response(RapSerializer(raps, many=True).data)

    def post(self, request, id_proyecto):
        proyecto = self._get_proyecto(id_proyecto)
        if proyecto.id_curso.id_docente_id != request.user.id:
            return Response(
                {'detail': 'Solo el docente propietario puede crear RAPs en este proyecto.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RapCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rap = serializer.save(proyecto=proyecto)
        return Response(RapSerializer(rap).data, status=status.HTTP_201_CREATED)


class RapDetailView(APIView):
    """
    PUT    /api/raps/<id>/ — actualiza RAP (solo docente propietario).
    DELETE /api/raps/<id>/ — elimina RAP si no tiene criterios vinculados.
    """
    authentication_classes = [UsuarioJWTAuthentication]

    def _get_rap(self, id):
        return get_object_or_404(
            ResultadoAprendizaje.objects.select_related('proyecto__id_curso'),
            pk=id,
        )

    def _es_docente_propietario(self, rap, user):
        return rap.proyecto.id_curso.id_docente_id == user.id

    def put(self, request, id):
        rap = self._get_rap(id)
        if not self._es_docente_propietario(rap, request.user):
            return Response(
                {'detail': 'Solo el docente propietario puede editar este RAP.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RapCreateSerializer(rap, data=request.data)
        serializer.is_valid(raise_exception=True)
        rap = serializer.save()
        return Response(RapSerializer(rap).data)

    def delete(self, request, id):
        rap = self._get_rap(id)
        if not self._es_docente_propietario(rap, request.user):
            return Response(
                {'detail': 'Solo el docente propietario puede eliminar este RAP.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        rap.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Fases del proyecto
# ---------------------------------------------------------------------------

class FaseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/proyectos/<proyecto_id>/fases/ — Lista fases del proyecto ordenadas por campo orden.
         Accesible para docente propietario, administrador y estudiantes activos del curso.
    POST /api/proyectos/<proyecto_id>/fases/ — Crea una fase (solo el docente propietario).
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FaseCreateSerializer
        return FaseSerializer

    def _get_proyecto(self):
        return get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=self.kwargs['proyecto_id'],
        )

    def _check_acceso_proyecto(self, proyecto):
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
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
        proyecto = self._get_proyecto()
        self._check_acceso_proyecto(proyecto)
        return FaseProyecto.objects.filter(id_proyecto=proyecto).order_by('orden')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['proyecto'] = self._get_proyecto()
        return context

    def perform_create(self, serializer):
        proyecto = self._get_proyecto()
        if proyecto.id_curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')
        fase = serializer.save(id_proyecto=proyecto)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='fases',
            descripcion=f'Fase creada: ID={fase.id}, nombre={fase.nombre}, proyecto ID={proyecto.id}',
        )


class FaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/fases/<pk>/ — Detalle de la fase.
    PUT    /api/fases/<pk>/ — Actualiza todos los campos de la fase.
    PATCH  /api/fases/<pk>/ — Actualización parcial.
    DELETE /api/fases/<pk>/ — Elimina la fase (409 si tiene actividades asociadas).

    Solo el docente propietario del curso puede modificar o eliminar.
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            FaseProyecto.objects
            .filter(id_proyecto__id_curso__id_docente=self.request.user)
            .select_related('id_proyecto__id_curso')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FaseUpdateSerializer
        return FaseSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.actividades.exists():
            return Response(
                {'detail': 'No se puede eliminar la fase porque tiene actividades asociadas.'},
                status=status.HTTP_409_CONFLICT,
            )
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='fases',
            descripcion=f'Fase eliminada: ID={instance.id}, nombre={instance.nombre}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Actividades
# ---------------------------------------------------------------------------

class ActividadListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/fases/<fase_id>/actividades/ — lista actividades de la fase.
         Accesible para todos los participantes del curso (docente, admin, estudiantes activos).
    POST /api/fases/<fase_id>/actividades/ — crea actividad (solo el docente propietario).
    """

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsDocente()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ActividadCreateSerializer
        return ActividadSerializer

    def _get_fase(self):
        return get_object_or_404(
            FaseProyecto.objects.select_related('id_proyecto__id_curso'),
            pk=self.kwargs['fase_id'],
        )

    def _check_acceso_fase(self, fase):
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = fase.id_proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
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
        fase = self._get_fase()
        self._check_acceso_fase(fase)
        return Actividad.objects.filter(id_fase=fase)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['fase'] = self._get_fase()
        return context

    def perform_create(self, serializer):
        fase = self._get_fase()
        if fase.id_proyecto.id_curso.id_docente_id != self.request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')
        actividad = serializer.save(id_fase=fase)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='actividades',
            descripcion=f'Actividad creada: ID={actividad.id}, nombre={actividad.nombre}, fase ID={fase.id}',
        )


class ActividadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/actividades/<pk>/ — detalle de la actividad.
    PUT    /api/actividades/<pk>/ — actualiza todos los campos.
    PATCH  /api/actividades/<pk>/ — actualización parcial.
    DELETE /api/actividades/<pk>/ — elimina si no hay dependencias activas (409 si las hay).

    Solo el docente propietario del curso puede modificar o eliminar.
    El queryset filtra transitivamente: actividad → fase → proyecto → curso → docente.
    """

    permission_classes = [EsDocente]

    def get_queryset(self):
        return (
            Actividad.objects
            .filter(id_fase__id_proyecto__id_curso__id_docente=self.request.user)
            .select_related('id_fase__id_proyecto__id_curso')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ActividadUpdateSerializer
        return ActividadSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sucesores.exists():
            return Response(
                {'detail': 'No se puede eliminar la actividad porque otras actividades dependen de ella.'},
                status=status.HTTP_409_CONFLICT,
            )
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='actividades',
            descripcion=f'Actividad eliminada: ID={instance.id}, nombre={instance.nombre}',
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActividadAsignarResponsableView(generics.UpdateAPIView):
    """
    PATCH /api/actividades/<pk>/asignar-responsable/

    Permite al líder de equipo asignar el responsable de una actividad.
    El responsable debe ser miembro activo del equipo asignado a la actividad.
    """

    http_method_names = ['patch']
    permission_classes = [EsLiderEquipo]
    serializer_class = ActividadAsignarResponsableSerializer

    def get_queryset(self):
        return (
            Actividad.objects
            .filter(
                id_equipo_asignado__miembros__usuario=self.request.user,
                id_equipo_asignado__miembros__estado='activo',
                id_equipo_asignado__miembros__rol_interno='lider',
            )
            .select_related('id_equipo_asignado')
            .distinct()
        )

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


def _recalcular_porcentaje_fase(fase):
    """BE 04 — Recalcula porcentaje_completado de la fase como promedio del último avance por actividad.

    Emite exactamente 2 queries: una de agregación y una UPDATE.
    """
    ultimo_avance_sq = (
        AvanceActividad.objects
        .filter(id_actividad=OuterRef('pk'))
        .order_by('-fecha_registro')
        .values('porcentaje_completado')[:1]
    )
    resultado = (
        Actividad.objects
        .filter(id_fase=fase)
        .annotate(ultimo_porcentaje=Coalesce(Subquery(ultimo_avance_sq), 0))
        .aggregate(total=Count('id'), suma=Sum('ultimo_porcentaje'))
    )
    total = resultado['total'] or 0
    nuevo_pct = round((resultado['suma'] or 0) / total) if total else 0
    FaseProyecto.objects.filter(pk=fase.pk).update(porcentaje_completado=nuevo_pct)


class AvanceActividadListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/actividades/<actividad_id>/avances/ — historial de avances (BE 03).
         Accesible a todos los participantes del proyecto.
    POST /api/actividades/<actividad_id>/avances/ — registra avance (BE 02).
         Solo responsable o miembro activo del equipo asignado.
         Actualiza automáticamente el estado de la actividad al 100%.
         Recalcula el porcentaje de completitud de la fase (BE 04).
    """

    permission_classes = [IsAuthenticated]

    def _get_actividad(self):
        if not hasattr(self, '_actividad_cache'):
            self._actividad_cache = get_object_or_404(
                Actividad.objects.select_related(
                    'id_fase__id_proyecto__id_curso',
                    'id_equipo_asignado',
                ),
                pk=self.kwargs['actividad_id'],
            )
        return self._actividad_cache

    def _verificar_acceso(self, actividad):
        """Verifica que el usuario sea participante del proyecto (BE 03)."""
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = actividad.id_fase.id_proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
            en_proyecto = MiembroEquipo.objects.filter(
                equipo__proyecto__id_curso=curso,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not en_proyecto:
                raise PermissionDenied('No perteneces a ningún equipo de este proyecto.')
        else:
            raise PermissionDenied('Acceso no permitido.')

    def get_queryset(self):
        actividad = self._get_actividad()
        self._verificar_acceso(actividad)
        return AvanceActividad.objects.filter(id_actividad=actividad).select_related('id_usuario')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AvanceActividadCreateSerializer
        return AvanceActividadSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['actividad'] = self._get_actividad()
        return ctx

    def perform_create(self, serializer):
        actividad = self._get_actividad()
        self._verificar_acceso(actividad)
        avance = serializer.save(
            id_actividad=actividad,
            id_usuario=self.request.user,
        )
        # BE 02 — auto-completar actividad si llega al 100 %
        if avance.porcentaje_completado == 100:
            Actividad.objects.filter(pk=actividad.pk).update(
                estado=Actividad.Estado.COMPLETADA
            )
        # BE 04 — recalcular porcentaje de la fase
        _recalcular_porcentaje_fase(actividad.id_fase)


# ---------------------------------------------------------------------------
# HU-016 — Asignación de responsables
# ---------------------------------------------------------------------------

class ActividadAsignarView(APIView):
    """
    PATCH /api/actividades/<pk>/asignar/

    Líder de equipo asigna uno o más responsables a una actividad.
    Si la actividad no tiene equipo asignado, se auto-asigna el equipo del líder.
    Los responsables deben ser miembros activos de ese equipo.
    """

    permission_classes = [EsLiderEquipo]

    def _get_equipo_lider(self):
        membresia = (
            MiembroEquipo.objects
            .filter(usuario=self.request.user, estado='activo', rol_interno='lider')
            .select_related('equipo__proyecto')
            .first()
        )
        if not membresia:
            raise PermissionDenied('No eres líder activo de ningún equipo.')
        return membresia.equipo

    def patch(self, request, pk):
        equipo = self._get_equipo_lider()
        actividad = get_object_or_404(
            Actividad.objects
            .filter(id_fase__id_proyecto=equipo.proyecto)
            .select_related('id_equipo_asignado'),
            pk=pk,
        )
        # Auto-asignar el equipo si todavía no tiene uno
        if actividad.id_equipo_asignado is None:
            actividad.id_equipo_asignado = equipo
            actividad.save(update_fields=['id_equipo_asignado'])

        serializer = ActividadAsignarSerializer(
            data=request.data,
            context={'actividad': actividad, 'request': request},
        )
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['responsables']
        actividad.responsables.set(ids)
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='actividades',
            descripcion=f'Responsables asignados a actividad ID={actividad.id}: {ids}',
        )
        return Response(ActividadSerializer(actividad).data)


class ActividadesPorEquipoView(generics.ListAPIView):
    """
    GET /api/equipos/<equipo_id>/actividades/

    Lista todas las actividades asignadas al equipo.
    El campo `es_responsable` indica si el usuario autenticado es responsable.
    Accesible a miembros activos del equipo, docentes del curso y administradores.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ActividadPorEquipoSerializer

    def get_queryset(self):
        from apps.equipos.models import Equipo
        equipo = get_object_or_404(Equipo, pk=self.kwargs['equipo_id'])
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            pass
        elif tipo_rol == 'docente':
            if not equipo.proyecto.id_curso.id_docente_id == usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
            es_miembro = MiembroEquipo.objects.filter(
                equipo=equipo,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not es_miembro:
                raise PermissionDenied('No eres miembro activo de este equipo.')
        else:
            raise PermissionDenied('Acceso no permitido.')
        return (
            Actividad.objects
            .filter(id_fase__id_proyecto=equipo.proyecto)
            .prefetch_related(
                'responsables',
                Prefetch('avances', queryset=AvanceActividad.objects.order_by('-fecha_registro')),
            )
            .select_related('id_fase')
        )
# BE 01 — Progreso del proyecto
# ---------------------------------------------------------------------------

class ProyectoProgresoView(APIView):
    """
    GET /api/proyectos/<pk>/progreso/

    Retorna el resumen de progreso del proyecto:
      - porcentaje_progreso: promedio del porcentaje_completado de todas sus fases.
      - fases: lista ordenada con conteos de actividades por estado por fase.
      - actividades_por_estado: conteos globales (pendiente / en_progreso / completada / bloqueada).

    Acceso: administrador, docente propietario del curso o estudiante activo del curso.
    """

    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _check_acceso(self, proyecto):
        """Verifica que el usuario autenticado tenga acceso al progreso del proyecto.

        Reglas de negocio:
            - Administrador: acceso irrestricto.
            - Docente: solo si es el propietario del curso al que pertenece el proyecto.
            - Estudiante / lider_equipo: solo si pertenece activamente a algún
              equipo cuyo proyecto esté vinculado al mismo curso.
            - Cualquier otro rol: acceso denegado.

        Args:
            proyecto: Instancia de Proyecto con id_curso ya seleccionado
                      (se espera select_related('id_curso')).

        Raises:
            PermissionDenied: Si el usuario no cumple ninguna de las reglas de acceso.
        """
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
            tiene_acceso = MiembroEquipo.objects.filter(
                equipo__proyecto__id_curso=curso,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not tiene_acceso:
                raise PermissionDenied('No perteneces a ningún equipo de este curso.')
        else:
            raise PermissionDenied('Acceso no permitido.')

    def get(self, request, pk):
        proyecto = get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=pk,
        )
        self._check_acceso(proyecto)

        # 1. Fases con resumen de actividades por estado (porcentaje almacenado en FaseProyecto)
        fases = list(
            FaseProyecto.objects
            .filter(id_proyecto=proyecto)
            .con_resumen_actividades()
            .order_by('orden')
        )

        # 2. Actividades con detalle: equipo asignado + último avance registrado
        actividades_qs = (
            Actividad.objects
            .filter(id_fase__id_proyecto=proyecto)
            .select_related('id_equipo_asignado', 'id_fase')
            .prefetch_related(
                Prefetch(
                    'avances',
                    queryset=AvanceActividad.objects.order_by('-fecha_registro'),
                    to_attr='avances_ordenados',
                )
            )
            .order_by('id_fase__orden', 'id')
        )
        actividades_por_fase = {}
        for act in actividades_qs:
            actividades_por_fase.setdefault(act.id_fase_id, []).append(act)

        # 3. Equipos con conteo de actividades por estado y número de miembros activos
        equipos_qs = (
            Equipo.objects
            .filter(proyecto=proyecto)
            .annotate(
                actividades_total=Count('actividades', distinct=True),
                actividades_completadas=Count(
                    'actividades',
                    filter=Q(actividades__estado='completada'),
                    distinct=True,
                ),
                actividades_en_progreso=Count(
                    'actividades',
                    filter=Q(actividades__estado='en_progreso'),
                    distinct=True,
                ),
                actividades_bloqueadas=Count(
                    'actividades',
                    filter=Q(actividades__estado='bloqueada'),
                    distinct=True,
                ),
                num_miembros=Count(
                    'miembros',
                    filter=Q(miembros__estado='activo'),
                    distinct=True,
                ),
            )
            .order_by('nombre')
        )

        # Construir datos de fases con actividades anidadas
        porcentaje_progreso = (
            round(sum(f.porcentaje_completado for f in fases) / len(fases))
            if fases else 0
        )
        fases_data = []
        totales = {'pendiente': 0, 'en_progreso': 0, 'completada': 0, 'bloqueada': 0}
        for f in fases:
            pendientes = max(
                f.total_actividades
                - f.actividades_completadas
                - f.actividades_en_progreso
                - f.actividades_bloqueadas,
                0,
            )
            totales['pendiente'] += pendientes
            totales['en_progreso'] += f.actividades_en_progreso
            totales['completada'] += f.actividades_completadas
            totales['bloqueada'] += f.actividades_bloqueadas

            actividades_detalle = []
            for act in actividades_por_fase.get(f.id, []):
                ultimo = act.avances_ordenados[0] if act.avances_ordenados else None
                eq = act.id_equipo_asignado
                actividades_detalle.append({
                    'id': act.id,
                    'nombre': act.nombre,
                    'estado': act.estado,
                    'prioridad': act.prioridad,
                    'fecha_limite': act.fecha_limite,
                    'equipo_asignado': {'id': eq.id, 'nombre': eq.nombre} if eq else None,
                    'ultimo_avance': {
                        'porcentaje_completado': ultimo.porcentaje_completado,
                        'descripcion': ultimo.descripcion,
                        'fecha_registro': ultimo.fecha_registro,
                    } if ultimo else None,
                })

            fases_data.append({
                'id': f.id,
                'nombre': f.nombre,
                'orden': f.orden,
                'estado': f.estado,
                'porcentaje_completado': f.porcentaje_completado,
                'total_actividades': f.total_actividades,
                'actividades_completadas': f.actividades_completadas,
                'actividades_en_progreso': f.actividades_en_progreso,
                'actividades_bloqueadas': f.actividades_bloqueadas,
                'actividades_pendientes': pendientes,
                'actividades': actividades_detalle,
            })

        # Construir datos de equipos
        equipos_data = []
        for eq in equipos_qs:
            pendientes_eq = max(
                eq.actividades_total
                - eq.actividades_completadas
                - eq.actividades_en_progreso
                - eq.actividades_bloqueadas,
                0,
            )
            porcentaje_eq = (
                round(eq.actividades_completadas / eq.actividades_total * 100)
                if eq.actividades_total else 0
            )
            equipos_data.append({
                'id': eq.id,
                'nombre': eq.nombre,
                'estado': eq.estado,
                'num_miembros': eq.num_miembros,
                'actividades_total': eq.actividades_total,
                'actividades_completadas': eq.actividades_completadas,
                'actividades_en_progreso': eq.actividades_en_progreso,
                'actividades_pendientes': pendientes_eq,
                'actividades_bloqueadas': eq.actividades_bloqueadas,
                'porcentaje_progreso': porcentaje_eq,
            })

        return Response({
            'id_proyecto': proyecto.pk,
            'nombre': proyecto.nombre,
            'estado': proyecto.estado,
            'porcentaje_progreso': porcentaje_progreso,
            'total_fases': len(fases),
            'fases': fases_data,
            'actividades_por_estado': totales,
            'equipos': equipos_data,
        })


# ---------------------------------------------------------------------------
# HU-28 BE-01 — Dashboard del proyecto (solo docente)
# ---------------------------------------------------------------------------

class ProyectoDashboardView(APIView):
    """
    GET /api/proyectos/<proyecto_id>/dashboard/

    Resumen ejecutivo del proyecto para el docente propietario:
      - progreso_general  : métricas de vista_progreso_proyecto
      - fases             : lista ordenada de vista_progreso_fase
      - entregables_resumen: métricas de vista_entregables_proyecto
      - evaluaciones_completadas: evaluaciones en estado publicada
      - actividad_reciente: últimos 10 registros de avance_actividad
    """

    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def get(self, request, proyecto_id):
        proyecto = get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=proyecto_id,
        )
        if proyecto.id_curso.id_docente_id != request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')

        # 1. progreso_general desde vista_progreso_proyecto
        try:
            vpp = VistaProgresoProyecto.objects.get(id_proyecto=proyecto_id)
            progreso_general = {
                'porcentaje_progreso': vpp.porcentaje_progreso,
                'total_fases': vpp.total_fases,
                'fases_completadas': vpp.fases_completadas,
                'fases_en_progreso': vpp.fases_en_progreso,
                'total_actividades': vpp.total_actividades,
                'actividades_completadas': vpp.actividades_completadas,
            }
        except VistaProgresoProyecto.DoesNotExist:
            progreso_general = {
                'porcentaje_progreso': 0,
                'total_fases': 0,
                'fases_completadas': 0,
                'fases_en_progreso': 0,
                'total_actividades': 0,
                'actividades_completadas': 0,
            }

        # 2. fases desde vista_progreso_fase
        fases = [
            {
                'id_fase': f.id_fase,
                'nombre_fase': f.nombre_fase,
                'estado_fase': f.estado_fase,
                'orden': f.orden,
                'porcentaje_almacenado': f.porcentaje_almacenado,
                'total_actividades': f.total_actividades,
                'actividades_completadas': f.actividades_completadas,
                'actividades_en_progreso': f.actividades_en_progreso,
                'actividades_bloqueadas': f.actividades_bloqueadas,
            }
            for f in VistaProgresoFase.objects.filter(id_proyecto=proyecto_id).order_by('orden')
        ]

        # 3. entregables_resumen desde vista_entregables_proyecto (raw SQL)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT total_entregables, aprobados, rechazados, enviados, pendientes, "
                "tasa_entrega_tiempo_pct FROM vista_entregables_proyecto WHERE proyecto_id = %s",
                [proyecto_id],
            )
            row = cursor.fetchone()
        if row:
            entregables_resumen = {
                'total_entregables': row[0],
                'aprobados': row[1],
                'rechazados': row[2],
                'enviados': row[3],
                'pendientes': row[4],
                'tasa_entrega_tiempo_pct': float(row[5]) if row[5] is not None else 0.0,
            }
        else:
            entregables_resumen = {
                'total_entregables': 0,
                'aprobados': 0,
                'rechazados': 0,
                'enviados': 0,
                'pendientes': 0,
                'tasa_entrega_tiempo_pct': 0.0,
            }

        # 4. evaluaciones completadas (estado 'publicada' equivale a completada en este esquema)
        from apps.evaluacion.models import Evaluacion
        evaluaciones_completadas = (
            Evaluacion.objects
            .filter(
                id_entregable__id_actividad__id_fase__id_proyecto_id=proyecto_id,
                estado='publicada',
            )
            .count()
        )

        # 5. actividad_reciente: últimos 10 avances del proyecto
        actividad_reciente = [
            {
                'id': a.id,
                'descripcion': a.descripcion,
                'porcentaje_completado': a.porcentaje_completado,
                'fecha_registro': a.fecha_registro,
                'tipo': a.tipo,
                'id_actividad_id': a.id_actividad_id,
            }
            for a in (
                AvanceActividad.objects
                .filter(id_actividad__id_fase__id_proyecto_id=proyecto_id)
                .order_by('-fecha_registro')[:10]
            )
        ]

        return Response({
            'progreso_general': progreso_general,
            'fases': fases,
            'entregables_resumen': entregables_resumen,
            'evaluaciones_completadas': evaluaciones_completadas,
            'actividad_reciente': actividad_reciente,
        })


# ---------------------------------------------------------------------------
# HU-28 BE-02 — Resumen de equipos del proyecto (solo docente)
# ---------------------------------------------------------------------------

class ProyectoEquiposResumenView(APIView):
    """
    GET /api/proyectos/<proyecto_id>/equipos-resumen/

    Por cada equipo del proyecto retorna métricas agregadas:
      - porcentaje_avance, entregables por estado, nota_promedio, alertas.
    Todo el cálculo se realiza con anotaciones ORM (sin loops en Python).
    """

    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [EsDocente]

    def get(self, request, proyecto_id):
        proyecto = get_object_or_404(
            Proyecto.objects.select_related('id_curso'),
            pk=proyecto_id,
        )
        if proyecto.id_curso.id_docente_id != request.user.pk:
            raise PermissionDenied('No eres el docente propietario de este proyecto.')

        hoy = timezone.now().date()
        dias_desde_inicio = (hoy - proyecto.fecha_inicio).days if proyecto.fecha_inicio else 0

        equipos_qs = (
            Equipo.objects
            .filter(proyecto_id=proyecto_id)
            .annotate(
                porcentaje_avance=Coalesce(
                    Avg('actividades__avances__porcentaje_completado'),
                    Value(0.0),
                    output_field=FloatField(),
                ),
                aprobados=Count(
                    'entregables',
                    filter=Q(entregables__estado='aprobado'),
                    distinct=True,
                ),
                rechazados=Count(
                    'entregables',
                    filter=Q(entregables__estado='rechazado'),
                    distinct=True,
                ),
                enviados=Count(
                    'entregables',
                    filter=Q(entregables__estado='enviado'),
                    distinct=True,
                ),
                pendientes=Count(
                    'entregables',
                    filter=Q(entregables__estado='borrador'),
                    distinct=True,
                ),
                nota_promedio=Avg('entregables__evaluaciones__puntuacion_total'),
                vencidas=Count(
                    'actividades',
                    filter=Q(actividades__fecha_limite__lt=hoy) & ~Q(actividades__estado='completada'),
                    distinct=True,
                ),
            )
            .order_by('nombre')
        )

        resultado = []
        for eq in equipos_qs:
            alertas = []
            if eq.vencidas:
                alertas.append(f'{eq.vencidas} actividad(es) vencida(s)')
            if eq.rechazados:
                alertas.append(f'{eq.rechazados} entregable(s) rechazado(s)')
            if eq.porcentaje_avance < 30 and dias_desde_inicio > 7:
                alertas.append('Avance bajo')

            resultado.append({
                'equipo_id': eq.id,
                'nombre': eq.nombre,
                'estado': eq.estado,
                'porcentaje_avance': round(float(eq.porcentaje_avance), 2),
                'entregables': {
                    'aprobados': eq.aprobados,
                    'rechazados': eq.rechazados,
                    'enviados': eq.enviados,
                    'pendientes': eq.pendientes,
                },
                'nota_promedio': round(float(eq.nota_promedio), 2) if eq.nota_promedio is not None else None,
                'alertas': alertas,
            })

        return Response(resultado)
