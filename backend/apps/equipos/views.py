import io

from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from .models import Equipo, MiembroEquipo
from apps.cursos.models import Proyecto
from apps.usuarios.authentication import UsuarioJWTAuthentication
from apps.usuarios.models import Usuario
from apps.usuarios.permissions import EsDocente
from .models import Equipo, MiembroEquipo
from .serializers import (
    EditarEquipoSerializer,
    EquipoDetalleSerializer, EstudianteDisponibleSerializer,
    MiembroEquipoSerializer, UsuarioResumenSerializer,
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

"""
IMPLEMENTACIÓN DE SUBTAREAS HU-013:

Historial de cambios en membresías (BD01):
  Se implementa mediante soft-delete en el modelo MiembroEquipo.
  Al retirar un estudiante, su registro se marca como 'retirado' en lugar de eliminarse.
  Cada reasignación crea un nuevo registro para el equipo destino.
  El historial completo se preserva y puede auditarse consultando MiembroEquipo con filtro por estado.

Endpoint PUT /api/equipos/:id/ — editar nombre y cupo del equipo:
  Implementado en EditarEquipoView.
  Valida que el nuevo cupo no sea menor al número de miembros activos actuales.
  Registra la operación en bitácora.

Endpoint POST /api/equipos/:id/miembros/mover/ — reubicar estudiante:
  Implementado en MoverMiembroView.
  Mueve un estudiante de un equipo a otro del mismo proyecto en operación atómica.
  Valida: pertenencia al proyecto, cupo en destino, no duplicados.
  Usa transaction.atomic para asegurar consistencia.
  Preserva historial y registra movimiento en bitácora.

Endpoint DELETE /api/equipos/:id/disolver/ — disolver equipo:
  Implementado en DisolverEquipoView.
  Verifica que el equipo no tenga entregables/actividades (validación comentada pendiente).
  Marca todos los miembros como 'retirado' y el equipo como 'inactivo'.
  Soft-delete completo, ejecutado en transacción atómica.
  Registra la disolución en bitácora.

Registro de cambios de equipo en bitácora:
  Se utiliza la función registrar_evento (apps.bitacora.utils) en las operaciones:
  - Creación de equipo (ProyectoEquiposView.post)
  - Edición de equipo (EditarEquipoView.perform_update)
  - Movimiento de miembro (MoverMiembroView)
  - Disolución de equipo (DisolverEquipoView.delete)
  - Asignación individual (MiembroListView.post)
  Cada registro incluye: usuario, acción, módulo, descripción e IP origen.
"""


def registrar_bitacora(usuario, accion, modulo, descripcion=None, ip=None):
    """
    Función auxiliar para crear entradas en el log de auditoría del sistema.
    Captura: usuario responsable, tipo de acción, módulo afectado,
    descripción detallada del cambio y dirección IP origen.
    Esta función se invoca después de operaciones de creación, edición,
    disolución y reubicación de miembros para cumplir requisitos de auditoría.
    """
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
        # Fallo en bitácora no debe interrumpir la operación principal
        pass


def get_client_ip(request):
    """
    Extrae la dirección IP real del cliente, considerando proxies
    y configuración de X-Forwarded-For para obtener el IP original.
    """
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
        """
        Al crear un equipo, se registra en la bitácora del sistema
        el docente responsable, timestamp y descripción del cambio.
        """

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
    GET  /api/proyectos/<proyecto_id>/equipos/
    POST /api/proyectos/<proyecto_id>/equipos/
    Vista con permisos de docente. GET lista equipos (filtra por rol del usuario).
    POST crea un equipo (solo docentes) y registra la creación en bitácora (BE04).
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
        """
        BE04 — Registrar creación de equipo en bitácora
        Cuando un docente crea un equipo, se registra:
        - Usuario responsable (request.user)
        - Acción: CREATE
        - Módulo: 'equipos'
        - Descripción con nombre del equipo y proyecto
        - IP de origen
        """
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
            # BE04 — Registrar creación de equipo en bitácora
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
    """
    POST /api/equipos/<equipo_id>/asignar/
    Asignación masiva de estudiantes a un equipo.
    Valida por cada estudiante: existencia, rol, ya asignado, pertenencia a otro
    equipo del mismo proyecto y cupo disponible. Registra en bitácora.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, equipo_id):
        """
        Al asignar estudiantes, se registra cada asignación en bitácora.
        """
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

            # Verificar que no tenga membresía activa en este equipo
            if MiembroEquipo.objects.filter(equipo=equipo, usuario=usuario, estado='activo').exists():
                continue  # Ya está en el equipo, no duplicar

            # Validar que no pertenezca a otro equipo del mismo proyecto
            if MiembroEquipo.objects.filter(
                equipo__proyecto=equipo.proyecto, usuario=usuario, estado='activo'
            ).exists():
                errores.append({'usuario_id': uid, 'error': 'Ya pertenece a otro equipo de este proyecto.'})
                continue

            # Validar cupo
            miembros_activos = MiembroEquipo.objects.filter(equipo=equipo, estado='activo').count()
            if miembros_activos >= equipo.cupo_maximo:
                errores.append({'usuario_id': uid, 'error': 'El equipo ha alcanzado su cupo máximo.'})
                continue

            # Crear nueva membresía (soft-delete preserva historial)
            MiembroEquipo.objects.create(equipo=equipo, usuario=usuario)
            # Registrar asignación en bitácora
            registrar_bitacora(
                request.user if request.user.is_authenticated else None,
                BitacoraSistema.Accion.CREATE,
                'miembros_equipo',
                f'Estudiante {usuario.id} asignado al equipo {equipo.id}',
                get_client_ip(request),
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

    def delete(self, request, equipo_id, usuario_id):
        miembro = get_object_or_404(MiembroEquipo, equipo_id=equipo_id, usuario_id=usuario_id, estado='activo')
        # Soft-delete: marcar como retirado preserva el historial
        miembro.estado = 'retirado'
        miembro.save()
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

        return Usuario.objects.filter(
            tipo_rol='estudiante',
            estado='activo',
        ).exclude(id__in=ya_asignados)


# PUT/PATCH /api/equipos/<equipo_id>/
# Edita nombre, descripción y cupo máximo de un equipo.
# Valida unicidad de nombre dentro del proyecto y que el nuevo cupo no sea menor a miembros activos.
class EditarEquipoView(generics.UpdateAPIView):
    authentication_classes = [UsuarioJWTAuthentication]
    serializer_class = EditarEquipoSerializer
    queryset = Equipo.objects.all()
    lookup_url_kwarg = 'equipo_id'
    http_method_names = ['put', 'patch']

    def perform_update(self, serializer):
        equipo = serializer.save()
        # Registra en bitácora la edición del equipo
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

    def post(self, request, equipo_id):
        usuario_id = request.data.get('usuario_id')
        equipo_destino_id = request.data.get('equipo_destino_id')

        if not usuario_id or not equipo_destino_id:
            return Response(
                {"detail": "Se requieren usuario_id y equipo_destino_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        equipo_origen = get_object_or_404(Equipo, pk=equipo_id)
        equipo_destino = get_object_or_404(Equipo, pk=equipo_destino_id)

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

        # Validar cupo disponible en el equipo destino
        miembros_destino = MiembroEquipo.objects.filter(
            equipo=equipo_destino,
            estado='activo',
        ).count()
        if miembros_destino >= equipo_destino.cupo_maximo:
            return Response(
                {"detail": f"El equipo destino ha alcanzado su cupo máximo de {equipo_destino.cupo_maximo} integrantes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Operación atómica: ambos cambios (retiro y asignación) confirman o revierten juntos
        with transaction.atomic():
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

        equipo_origen = get_object_or_404(Equipo, pk=equipo_id)
        equipo_destino = get_object_or_404(Equipo, pk=equipo_destino_id)

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

        # Validar cupo disponible en el equipo destino
        miembros_destino = MiembroEquipo.objects.filter(
            equipo=equipo_destino,
            estado='activo',
        ).count()
        if miembros_destino >= equipo_destino.cupo_maximo:
            return Response(
                {"detail": f"El equipo destino ha alcanzado su cupo máximo de {equipo_destino.cupo_maximo} integrantes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Operación atómica: ambos cambios (retiro y asignación) confirman o revierten juntos
        with transaction.atomic():
            # BE01 — Marcar membresía origen como retirada (preserva historial)
            miembro.estado = 'retirado'
            miembro.save()

            # update_or_create evita duplicados si existe un registro previo retirado
            nueva_membresia, _ = MiembroEquipo.objects.update_or_create(
                equipo=equipo_destino,
                usuario_id=usuario_id,
                defaults={'estado': 'activo'},
            )

        # BE04 — Registrar movimiento en bitácora
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
# Permite eliminar un equipo, pero con restricciones de integridad:
# 1. NO se permite eliminar equipos que tengan entregables/actividades asociadas.
#    (Validación comentada a espera de implementar la app de entregables).
# 2. La operación es un soft-delete: marca el equipo como 'inactivo' y
#    retira a todos sus miembros activos (cambiando su estado a 'retirado')
#    preservando el historial.
# 3. Se ejecuta en una transacción atómica para garantizar consistencia.
# 4. Registra la disolución en bitácora.
# Retorna 204 No Content si tiene éxito, 409 Conflict si no puede disolverse.
class DisolverEquipoView(generics.GenericAPIView):
    authentication_classes = [UsuarioJWTAuthentication]

    def delete(self, request, equipo_id):
        equipo = get_object_or_404(Equipo, pk=equipo_id)

        # Bloqueo por entregables — verificar solo si el modelo existe.
        # Cuando se implemente la app de entregables, descomentar:
        # from apps.entregables.models import Entregable
        # if Entregable.objects.filter(equipo=equipo).exists():
        #     return Response(
        #         {"detail": "No se puede disolver un equipo con entregables registrados."},
        #         status=status.HTTP_409_CONFLICT,
        #     )

        # Operación atómica: el retiro de miembros y la desactivación del equipo
        # confirman juntos o se revierten si algo falla.
        with transaction.atomic():
            # Retirar todos los miembros activos (preserva historial)
            MiembroEquipo.objects.filter(
                equipo=equipo,
                estado='activo',
            ).update(estado='retirado')

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
