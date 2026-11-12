import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.cursos.models import Actividad, Proyecto
from apps.entregables.models import Entregable
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from .models import Equipo, MiembroEquipo
from .permisos import exigir_gestion_proyecto
from .servicios import liberar_actividades_de_miembro
from .serializers import (
    ActualizarRolSerializer,
    EditarEquipoSerializer,
    EquipoDetalleSerializer,
    EquipoSerializer,
    EstudianteDisponibleSerializer,
    MiembroEquipoSerializer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Equipos por proyecto
# ---------------------------------------------------------------------------

class EquiposPorProyectoView(APIView):
    """
    GET  /api/proyectos/<proyecto_id>/equipos/
    POST /api/proyectos/<proyecto_id>/equipos/
    Vista genérica para listar y crear equipos de un proyecto.
    GET retorna detalle completo de equipos con sus miembros.
    POST crea un nuevo equipo y registra la operación en bitácora (BE04).
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

        exigir_gestion_proyecto(request.user, proyecto)

        serializer = EquipoSerializer(data=request.data, context={'request': request, 'proyecto': proyecto})
        if serializer.is_valid():
            try:
                equipo = serializer.save(proyecto=proyecto)
            except DjangoValidationError as exc:
                raise ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages})
            registrar_evento(
                request=request,
                accion=BitacoraSistema.Accion.CREATE,
                modulo='equipos',
                descripcion=f"Crear equipo '{equipo.nombre}' en proyecto {proyecto.nombre}",
            )
            equipo_con_miembros = Equipo.objects.prefetch_related('miembros__usuario').get(pk=equipo.pk)
            return Response(EquipoDetalleSerializer(equipo_con_miembros).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Estudiantes del equipo
# ---------------------------------------------------------------------------

class EstudiantesEquipoView(APIView):
    """
    GET /api/equipos/<equipo_id>/estudiantes/
    Retorna lista de estudiantes clasificados por su relación con el equipo:
    - 'disponibles': estudiantes sin equipo en este proyecto.
    - 'ya_en_equipo': estudiantes que ya son miembros activos de este equipo.
    - 'en_otro_equipo': estudiantes que pertenecen a otro equipo del mismo proyecto.
    Solo considera membresías con estado='activo' para la clasificación.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, equipo_id):
        try:
            equipo = Equipo.objects.select_related('proyecto').get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        proyecto = equipo.proyecto

        # BD01 — Filtrar solo miembros activos para determinar pertenencia actual
        ids_en_equipo = set(
            MiembroEquipo.objects.filter(equipo=equipo, estado='activo')
            .values_list('usuario_id', flat=True)
        )
        ids_otro_equipo = set(
            MiembroEquipo.objects.filter(equipo__proyecto=proyecto, estado='activo')
            .exclude(equipo=equipo)
            .values_list('usuario_id', flat=True)
        )

        todos = Usuario.objects.filter(tipo_rol__in=('estudiante', 'lider_equipo'), estado='activo').order_by('nombre', 'apellido')
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
    """
    POST /api/equipos/<equipo_id>/asignar/
    Asignación masiva de estudiantes a un equipo (docente dueño, director o administrador).
    Valida por cada estudiante: existencia, rol, ya asignado, pertenencia a otro
    equipo del mismo proyecto y cupo disponible. Registra en bitácora.
    El equipo se bloquea durante la operación para que el cupo no se pueda superar
    con peticiones simultáneas.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, equipo_id):
        """
        Al asignar estudiantes, se registra cada asignación en bitácora.
        """
        try:
            equipo = Equipo.objects.select_related('proyecto__id_curso').get(pk=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'detail': 'Equipo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        exigir_gestion_proyecto(request.user, equipo.proyecto)

        usuario_ids = request.data.get('usuarios', [])
        if not usuario_ids:
            return Response({'detail': 'No se proporcionaron usuarios.'}, status=status.HTTP_400_BAD_REQUEST)

        asignados = 0
        errores = []

        with transaction.atomic():
            # Bloqueo de fila: serializa las asignaciones concurrentes al mismo equipo.
            equipo = Equipo.objects.select_for_update().get(pk=equipo.pk)

            for uid in usuario_ids:
                try:
                    usuario = Usuario.objects.get(pk=uid, tipo_rol__in=('estudiante', 'lider_equipo'))
                except (Usuario.DoesNotExist, ValueError, TypeError):
                    errores.append({'usuario_id': uid, 'error': 'Estudiante no encontrado.'})
                    continue

                # Verificar que no tenga membresía activa en este equipo
                if MiembroEquipo.objects.filter(equipo=equipo, usuario=usuario, estado='activo').exists():
                    continue  # Ya está en el equipo, no duplicar

                # Validar que no pertenezca a otro equipo del mismo proyecto
                if MiembroEquipo.objects.filter(
                    equipo__proyecto=equipo.proyecto, usuario=usuario, estado='activo'
                ).exists():
                    errores.append({'usuario_id': uid, 'error': 'Ya pertenece a otro equipo de este proyecto.'})
                    continue

                # Validar cupo (con el equipo bloqueado, el conteo es confiable)
                miembros_activos = MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count()
                if miembros_activos >= equipo.cupo_maximo:
                    errores.append({'usuario_id': uid, 'error': 'El equipo ha alcanzado su cupo máximo.'})
                    continue

                # Crear o reactivar membresía (update_or_create evita duplicados por unique_together)
                try:
                    MiembroEquipo.objects.update_or_create(
                        equipo=equipo,
                        usuario=usuario,
                        defaults={'estado': 'activo'},
                    )
                except DjangoValidationError as exc:
                    errores.append({'usuario_id': uid, 'error': ' '.join(exc.messages)})
                    continue
                registrar_evento(
                    request=request,
                    accion=BitacoraSistema.Accion.CREATE,
                    modulo='miembros_equipo',
                    descripcion=f'Estudiante {usuario.id} asignado al equipo {equipo.id}',
                )
                asignados += 1

        return Response({'asignados': asignados, 'errores': errores}, status=status.HTTP_200_OK)


class RetirarMiembroView(generics.GenericAPIView):
    """
    DELETE /api/equipos/<equipo_id>/miembros/<usuario_id>/
    Implementa soft-delete: cambia el estado de la membresía a 'retirado'
    en lugar de eliminar el registro, preservando el historial.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, equipo_id, usuario_id):
        miembro = get_object_or_404(
            MiembroEquipo.objects.select_related('equipo__proyecto__id_curso'),
            equipo_id=equipo_id, usuario_id=usuario_id, estado='activo',
        )
        exigir_gestion_proyecto(request.user, miembro.equipo.proyecto)
        # Soft-delete: marcar como retirado preserva el historial. La señal post_save
        # deja sin responsable las actividades del miembro (ver signals.py).
        miembro.estado = 'retirado'
        miembro.save()
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='equipos',
            descripcion=f"Usuario id={usuario_id} retirado del equipo '{miembro.equipo.nombre}'.",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActualizarRolView(generics.UpdateAPIView):
    """
    PATCH /api/equipos/<equipo_id>/miembros/<usuario_id>/rol/
    Actualiza el rol interno y descripción de responsabilidades de un miembro.
    Validación: solo el propio usuario puede modificar su rol.
    Validación (serializer): solo un miembro puede tener rol 'lider' por equipo.
    """
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = ActualizarRolSerializer
    http_method_names = ['patch']

    def get_object(self):
        return get_object_or_404(
            MiembroEquipo,
            equipo_id=self.kwargs['equipo_id'],
            usuario_id=self.kwargs['usuario_id'],
            estado='activo',
            # Solo se pueden modificar membresías activas
        )

    def patch(self, request, *args, **kwargs):
        miembro = self.get_object()
        # BE04 — Solo el usuario dueño de la membresía puede actualizar su rol
        if request.user.id != miembro.usuario_id:
            return Response({'detail': 'Solo puedes actualizar tu propio rol.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(miembro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ActualizarRolMiembroView(APIView):
    """
    PATCH /api/miembros/<miembro_id>/
    Actualiza el rol_interno de un MiembroEquipo.
    Si el nuevo rol es 'lider', elimina el rol del lider anterior del mismo equipo.
    Enviar rol_interno vacío ("") para quitar el rol.
    Solo el docente dueño del curso, el director o el administrador pueden cambiarlo.
    Designar líder sincroniza Usuario.tipo_rol ('lider_equipo'), que el resto del
    sistema usa para los permisos del líder.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, miembro_id):
        miembro = get_object_or_404(
            MiembroEquipo.objects.select_related('usuario', 'equipo__proyecto__id_curso'),
            pk=miembro_id, estado='activo',
        )
        exigir_gestion_proyecto(request.user, miembro.equipo.proyecto)
        nuevo_rol = request.data.get('rol_interno', '')

        roles_validos = {'lider', 'desarrollador', 'analista', 'disenador', 'tester', ''}
        if nuevo_rol not in roles_validos:
            return Response({'detail': f'Rol inválido: {nuevo_rol}'}, status=status.HTTP_400_BAD_REQUEST)

        if nuevo_rol == 'lider':
            anteriores = MiembroEquipo.objects.filter(
                equipo__proyecto=miembro.equipo.proyecto,
                rol_interno='lider',
                estado='activo',
            ).exclude(pk=miembro_id)
            # Revertir rol de todos los líderes anteriores en una sola operación
            ids_anteriores = list(anteriores.values_list('usuario_id', flat=True))
            anteriores.update(rol_interno='')
            if ids_anteriores:
                Usuario.objects.filter(
                    pk__in=ids_anteriores, tipo_rol='lider_equipo'
                ).update(tipo_rol='estudiante')

        rol_anterior = miembro.rol_interno
        miembro.rol_interno = nuevo_rol
        miembro.save(update_fields=['rol_interno'])

        usuario = miembro.usuario
        if nuevo_rol == 'lider':
            usuario.tipo_rol = 'lider_equipo'
            usuario.save(update_fields=['tipo_rol'])
        elif rol_anterior == 'lider' and nuevo_rol != 'lider':
            # Solo revertir si antes era lider y ahora no lo es
            if usuario.tipo_rol == 'lider_equipo':
                usuario.tipo_rol = 'estudiante'
                usuario.save(update_fields=['tipo_rol'])

        return Response({'id': miembro.id, 'rol_interno': miembro.rol_interno})

# PUT/PATCH /api/equipos/<equipo_id>/
# Edita nombre, descripción y cupo máximo de un equipo.
# Valida unicidad de nombre dentro del proyecto y que el nuevo cupo no sea menor a miembros activos.
class EditarEquipoView(generics.UpdateAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = EditarEquipoSerializer
    queryset = Equipo.objects.select_related('proyecto__id_curso')
    lookup_url_kwarg = 'equipo_id'
    http_method_names = ['put', 'patch']

    def perform_update(self, serializer):
        exigir_gestion_proyecto(self.request.user, serializer.instance.proyecto)
        try:
            equipo = serializer.save()
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages})
        registrar_evento(
            request=self.request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='equipos',
            descripcion=f"Equipo '{equipo.nombre}' (id={equipo.id}) editado.",
        )


# POST /api/equipos/<equipo_id>/miembros/mover/
# Permite al docente mover un estudiante de un equipo a otro dentro del mismo proyecto
# en una única operación atómica (transaction.atomic). Validaciones:
# 1. El estudiante debe ser miembro activo del equipo origen.
# 2. Los equipos origen y destino deben pertenecer al mismo proyecto.
# 3. El equipo destino no debe superar su cupo máximo.
# 4. El estudiante no debe pertenecer ya al equipo destino.
# Implementación:
# - Marca la membresía original como 'retirado' (preserva historial).
# - Crea o reactiva (update_or_create) la membresía destino.
# - Registra el movimiento en bitácora.
class MoverMiembroView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, equipo_id):
        usuario_id = request.data.get('usuario_id')
        equipo_destino_id = request.data.get('equipo_destino_id')

        if not usuario_id or not equipo_destino_id:
            return Response(
                {"detail": "Se requieren usuario_id y equipo_destino_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        equipo_origen = get_object_or_404(Equipo.objects.select_related('proyecto__id_curso'), pk=equipo_id)
        equipo_destino = get_object_or_404(Equipo, pk=equipo_destino_id)

        exigir_gestion_proyecto(request.user, equipo_origen.proyecto)

        # Validar que ambos equipos pertenezcan al mismo proyecto
        if equipo_origen.proyecto_id != equipo_destino.proyecto_id:
            return Response(
                {"detail": "Los equipos deben pertenecer al mismo proyecto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener la membresía activa del estudiante en el equipo origen
        miembro = get_object_or_404(
            MiembroEquipo,
            equipo=equipo_origen,
            usuario_id=usuario_id,
            estado='activo',
        )

        # Operación atómica: el retiro y la asignación confirman o revierten juntos.
        # El equipo destino se bloquea para validar el cupo sin carreras.
        with transaction.atomic():
            equipo_destino = Equipo.objects.select_for_update().get(pk=equipo_destino.pk)
            miembros_destino = MiembroEquipo.objects.filter(
                equipo=equipo_destino,
                estado='activo',
            ).count()
            if miembros_destino >= equipo_destino.cupo_maximo:
                return Response(
                    {"detail": f"El equipo destino ha alcanzado su cupo máximo de {equipo_destino.cupo_maximo} integrantes."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Marcar membresía origen como retirada (preserva historial)
            miembro.estado = 'retirado'
            miembro.save()

            # update_or_create evita duplicados si existe un registro previo retirado
            nueva_membresia, _ = MiembroEquipo.objects.update_or_create(
                equipo=equipo_destino,
                usuario_id=usuario_id,
                defaults={'estado': 'activo'},
            )

        # Registrar movimiento en bitácora
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='equipos',
            descripcion=f"Usuario id={usuario_id} movido de equipo '{equipo_origen.nombre}' a '{equipo_destino.nombre}'.",
        )

        return Response(
            MiembroEquipoSerializer(nueva_membresia).data,
            status=status.HTTP_200_OK,
        )


# DELETE /api/equipos/<equipo_id>/disolver/
# Soft-delete de un equipo, con restricciones de integridad:
# 1. Responde 409 si el equipo tiene entregables registrados.
# 2. Marca el equipo como 'inactivo' y retira a todos sus miembros activos
#    (cambia su estado a 'retirado'), preservando el historial; las actividades
#    de esos miembros quedan sin responsable.
# 3. Se ejecuta en una transacción atómica y registra la disolución en bitácora.
# Retorna 204 No Content si tiene éxito.
class DisolverEquipoView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, equipo_id):
        equipo = get_object_or_404(Equipo.objects.select_related('proyecto__id_curso'), pk=equipo_id)
        exigir_gestion_proyecto(request.user, equipo.proyecto)

        if Entregable.objects.filter(id_equipo=equipo).exists():
            return Response(
                {"detail": "No se puede disolver un equipo con entregables registrados."},
                status=status.HTTP_409_CONFLICT,
            )

        # Operación atómica: el retiro de miembros y la desactivación del equipo
        # confirman juntos o se revierten si algo falla.
        with transaction.atomic():
            ids_miembros = list(
                MiembroEquipo.objects.filter(equipo=equipo, estado='activo')
                .values_list('usuario_id', flat=True)
            )
            # update() no dispara post_save: se liberan las actividades de forma explícita
            MiembroEquipo.objects.filter(equipo=equipo, estado='activo').update(estado='retirado')
            for uid in ids_miembros:
                liberar_actividades_de_miembro(equipo, uid, request=request)

            # Marcar el equipo como inactivo (soft-delete, no .delete())
            equipo.estado = 'inactivo'
            equipo.save()

        # Registrar disolución en bitácora
        registrar_evento(
            request=request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='equipos',
            descripcion=f"Equipo '{equipo.nombre}' (id={equipo.id}) disuelto.",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# BE 02 — Progreso del equipo
# ---------------------------------------------------------------------------

class EquipoProgresoView(APIView):
    """
    GET /api/equipos/<equipo_id>/progreso/

    Retorna el resumen de progreso del equipo:
      - Conteos globales de actividades asignadas al equipo por estado.
      - porcentaje_progreso: actividades_completadas / total * 100.
      - miembros: progreso individual de cada miembro activo según actividades
        en las que figura como responsable dentro de este equipo.

    Acceso: administrador, docente propietario del curso o miembro activo
    de cualquier equipo del mismo proyecto.
    """

    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _check_acceso(self, equipo):
        """Verifica que el usuario autenticado tenga derecho a consultar el progreso del equipo.

        Reglas de negocio:
            - Administrador: acceso irrestricto.
            - Docente: solo si es el propietario del curso al que pertenece el proyecto del equipo.
            - Estudiante / lider_equipo: solo si pertenece activamente a algún equipo
              del mismo proyecto (no necesariamente al equipo consultado).
            - Cualquier otro rol: acceso denegado.

        Args:
            equipo: Instancia de Equipo con su proyecto e id_curso ya seleccionados
                    (se espera select_related('proyecto__id_curso')).

        Raises:
            PermissionDenied: Si el usuario no cumple ninguna de las reglas de acceso.
        """
        usuario = self.request.user
        tipo_rol = getattr(usuario, 'tipo_rol', None)
        if tipo_rol == 'administrador':
            return
        curso = equipo.proyecto.id_curso
        if tipo_rol == 'docente':
            if curso.id_docente_id != usuario.pk:
                raise PermissionDenied('No eres el docente propietario de este proyecto.')
        elif tipo_rol in ('estudiante', 'lider_equipo'):
            tiene_acceso = MiembroEquipo.objects.filter(
                equipo__proyecto=equipo.proyecto,
                usuario=usuario,
                estado='activo',
            ).exists()
            if not tiene_acceso:
                raise PermissionDenied('No perteneces a ningún equipo de este proyecto.')
        else:
            raise PermissionDenied('Acceso no permitido.')

    def get(self, request, equipo_id):
        equipo = get_object_or_404(
            Equipo.objects.select_related('proyecto__id_curso'),
            pk=equipo_id,
        )
        self._check_acceso(equipo)
        proyecto = equipo.proyecto

        # Conteos globales: todas las actividades del proyecto (no solo las que
        # tienen id_equipo_asignado seteado, ya que muchas pueden no tenerlo)
        stats = (
            Actividad.objects
            .filter(id_fase__id_proyecto=proyecto)
            .aggregate(
                total=Count('id'),
                completadas=Count('id', filter=Q(estado='completada')),
                en_progreso=Count('id', filter=Q(estado='en_progreso')),
                bloqueadas=Count('id', filter=Q(estado='bloqueada')),
                pendientes=Count('id', filter=Q(estado='pendiente')),
            )
        )
        total = stats['total'] or 0
        completadas = stats['completadas'] or 0
        porcentaje = round(completadas * 100 / total) if total else 0

        # Progreso por miembro: actividades del proyecto donde el usuario figura
        # como id_responsable (FK) O en responsables (M2M), ambos campos válidos.
        miembros = (
            MiembroEquipo.objects
            .filter(equipo=equipo, estado='activo')
            .select_related('usuario')
            .order_by('usuario__nombre', 'usuario__apellido')
        )
        acts_proyecto = Actividad.objects.filter(id_fase__id_proyecto=proyecto)

        miembros_data = []
        for m in miembros:
            u = m.usuario
            acts_miembro = acts_proyecto.filter(
                Q(id_responsable=u) | Q(responsables=u)
            ).distinct()
            miembros_data.append({
                'id_usuario': u.pk,
                'nombre': f'{u.nombre} {u.apellido}',
                'rol_interno': m.rol_interno,
                'actividades_asignadas': acts_miembro.count(),
                'actividades_completadas': acts_miembro.filter(estado='completada').count(),
                'actividades_en_progreso': acts_miembro.filter(estado='en_progreso').count(),
                'actividades_pendientes': acts_miembro.filter(estado='pendiente').count(),
            })

        return Response({
            'id_equipo': equipo.pk,
            'nombre': equipo.nombre,
            'total_actividades': total,
            'actividades_completadas': completadas,
            'actividades_en_progreso': stats['en_progreso'] or 0,
            'actividades_bloqueadas': stats['bloqueadas'] or 0,
            'actividades_pendientes': stats['pendientes'] or 0,
            'porcentaje_progreso': porcentaje,
            'miembros': miembros_data,
        })


class MisEquiposView(APIView):
    authentication_classes = [UsuarioJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        membresias = MiembroEquipo.objects.filter(
            usuario=request.user, estado='activo'
        ).select_related('equipo', 'equipo__proyecto', 'equipo__proyecto__id_curso')

        resultado = []
        for m in membresias:
            equipo = m.equipo
            proyecto = equipo.proyecto
            actividades = (
                Actividad.objects
                .filter(
                    id_equipo_asignado=equipo,
                )
                .filter(
                    Q(responsables=request.user) | Q(id_responsable=request.user)
                )
                .select_related('id_fase').order_by('id_fase__orden', 'id').distinct()
            )
            fases = {}
            for actividad in actividades:
                fase = actividad.id_fase
                if fase.id not in fases:
                    fases[fase.id] = {
                        'id': fase.id,
                        'nombre': fase.nombre,
                        'orden': fase.orden,
                        'actividades': [],
                    }
                fases[fase.id]['actividades'].append({
                    'id': actividad.id,
                    'nombre': actividad.nombre,
                    'descripcion': actividad.descripcion,
                    'estado': actividad.estado,
                    'prioridad': actividad.prioridad,
                    'fecha_limite': str(actividad.fecha_limite) if actividad.fecha_limite else None,
                })
            resultado.append({
                'equipo': {'id': equipo.id, 'nombre': equipo.nombre},
                'proyecto': {'id': proyecto.id, 'nombre': proyecto.nombre},
                'curso': {'id': proyecto.id_curso.id, 'nombre': proyecto.id_curso.nombre},
                'fases': sorted(fases.values(), key=lambda f: f['orden']),
            })
        return Response(resultado)
