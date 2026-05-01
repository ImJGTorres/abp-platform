import io

from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.configuracion.models import PeriodoAcademico
from apps.equipos.models import MiembroEquipo
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer
from .models import Curso, ObjetivoProyecto, Proyecto
from .permissions import EsAdministrador, EsDocente, EsDocenteOAdministrador
from .serializers import (
    CursoAdminCreateSerializer,
    CursoAdminUpdateSerializer,
    CursoSerializer,
    CursoUpdateSerializer,
    ObjetivoSerializer,
    ObjetivoUpdateSerializer,
    ProyectoCreateSerializer,
    ProyectoSerializer,
    ProyectoUpdateSerializer,
)


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
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
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
        proyecto = serializer.save(id_curso=curso)
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='proyectos',
            descripcion=f'Proyecto creado: ID={proyecto.id}, nombre={proyecto.nombre}',
        )


class ProyectoDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/proyectos/<pk>/ — Detalle del proyecto.
    PUT   /api/proyectos/<pk>/ — Actualiza nombre, descripción, estado y fechas.
    PATCH /api/proyectos/<pk>/ — Actualización parcial.

    Solo el docente propietario del curso al que pertenece el proyecto puede modificarlo.
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


# ---------------------------------------------------------------------------
# Carga masiva de cursos (admin)
# ---------------------------------------------------------------------------

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

        elif tipo_rol == 'estudiante':
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
