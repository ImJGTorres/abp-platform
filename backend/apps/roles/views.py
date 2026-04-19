"""
Views para el módulo de Roles y Permisos.

Este archivo contiene todas las vistas (endpoints) para gestionar:
- Roles: crear, listar, actualizar, eliminar roles de usuario
- Permisos: crear, listar, actualizar, eliminar permisos
- RolPermiso: asignar y quitar permisos a roles

Estructura de URLs:
- /api/roles/           -> GET (lista), POST (crear)
- /api/roles/{id}/     -> GET, PUT, PATCH, DELETE (detalle de un rol)
- /api/roles/permisos/  -> GET, POST (lista/crear permisos)
- /api/roles/permisos/{id}/ -> GET, PUT, PATCH, DELETE (detalle de permiso)
- /api/roles/rol-permiso/ -> GET, POST (lista/crear relaciones)
- /api/roles/rol-permiso/{id}/ -> GET, DELETE (detalle/eliminar relación)
"""

from collections import defaultdict

from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento
from apps.usuarios.permissions import EsAdministrador

from apps.usuarios.models import UsuarioRol
from .models import Permiso, Rol, RolPermiso
from .serializers import PermisoSerializer, RolPermisoSerializer, RolSerializer



# ROL LIST CREATE VIEW - CRUD principal de Roles
#
# - /api/roles/ GET  -> Lista TODOS los roles (activos e inactivos)
# - /api/roles/ POST -> Crea un nuevo rol (asigna permisos)
#
# Autenticación: JWT requerida
# Permiso: EsAdministrador
#
# JSON de entrada para POST: Son los campos que estan en la clase Rol del archivo models.py de roles.
# JSON de respuesta: Devuelve los espacios que estan en la clase Meta del archivo serializers.py de roles.
#
# BE-03: Este endpoint implementa la creación de roles via POST
class RolListCreateView(APIView):
    # Solo administradores pueden acceder (no requiere auth específica para GET público si se quisiera)
    permission_classes = [EsAdministrador]

    # GET /api/roles/ - Lista todos los roles
    # Retorna lista de TODOS los roles (activos + inactivos)
    # Incluye los permisos de cada rol anidados en la respuesta
    def get(self, request):
        # Obtiene todos los roles, ordenados por nombre
        roles = Rol.objects.all().order_by('nombre')
        # Serializa usando RolSerializer (incluye permisos anidados)
        serializer = RolSerializer(roles, many=True)
        # Registra la consulta en bitácora
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='roles',
            descripcion='Consulta de lista de roles',
        )
        return Response(serializer.data)
    
    # POST /api/roles/ - Crea un nuevo rol
    # BE-03: Este método crea un nuevo rol en la base de datos.
    # 1. Recibe los datos del cliente (nombre, descripcion, permiso_ids)
    # 2. Valida con RolSerializer (verifica nombre único, permisos existen)
    # 3. Ejecuta create() del serializer que crea Rol + RolPermiso
    # 4. Registra en bitácora
    # 5. Retorna 201 con el rol creado
    def post(self, request):
        # Inicializa el serializer con los datos del request
        serializer = RolSerializer(data=request.data)
        # Valida los datos
        if not serializer.is_valid():
            # Retorna 400 con los errores de validación
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Ejecuta create() del serializer - crea rol y permisos en BD
        rol = serializer.save()
        codigos_asignados = list(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='roles',
            descripcion=(
                f'Rol creado: ID={rol.id}, nombre={rol.nombre}. '
                f'Permisos asignados: {codigos_asignados or "ninguno"}'
            ),
        )
        # Retorna 201 Created con el rol serializado
        return Response(RolSerializer(rol).data, status=status.HTTP_201_CREATED)

# ROL DETAIL VIEW - Ver/Actualizar/Eliminar un rol específico
# Endpoints para un rol específico por ID: /api/roles/{id}/
#
# - GET    /api/roles/{id}/    -> Ver detalle de un rol
# - PUT    /api/roles/{id}/    -> Atualización COMPLETA (reemplaza todo)
# - PATCH  /api/roles/{id}/    -> Atualización PARCIAL (solo campos enviados)
# - DELETE /api/roles/{id}/    -> Elimina el rol
#
# Para PUT/PATCH, el JSON es igual que POST pero con campos a actualizar.
# Si se envía "permiso_ids", se reemplazan TODOS los permisos.
class RolDetailView(APIView):
    permission_classes = [EsAdministrador]

    # _get_object() - Helper interno para obtener un rol por ID
    # Intenta obtener un rol de la BD por su ID.
    # Retorna el objeto Rol si existe, o None si no existe.
    # Se usa en todos los métodos para evitar código duplicado.
    def _get_object(self, pk):
        try:
            return Rol.objects.get(pk=pk)
        except Rol.DoesNotExist:
            return None

    # GET /api/roles/{id}/ - Ver detalle de un rol
    def get(self, request, pk):
        # Busca el rol por ID
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        # Registra en bitácora
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='roles',
            descripcion=f'Consulta de rol: ID={pk}',
        )
        # Retorna el rol serializado (incluye permisos anidados)
        return Response(RolSerializer(rol).data)

    # PUT /api/roles/{id}/ - Atualización completa
    # PUT reemplaza TODOS los campos del rol.
    # Si no envía un campo, ese campo queda vacío/null.
    def put(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        permisos_antes = set(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        # Serializa con instance=rol (indica que es update)
        serializer = RolSerializer(rol, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # save() llama update() del serializer
        serializer.save()
        permisos_despues = set(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        agregados = sorted(permisos_despues - permisos_antes)
        removidos = sorted(permisos_antes - permisos_despues)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='roles',
            descripcion=(
                f'Rol actualizado: ID={pk}, nombre={rol.nombre}. '
                f'Permisos agregados: {agregados or "ninguno"}. '
                f'Permisos removidos: {removidos or "ninguno"}'
            ),
        )
        return Response(serializer.data)

    # PATCH /api/roles/{id}/ - Atualización parcial
    # PATCH solo actualiza los campos enviados.
    # Los campos no enviados quedan iguales.
    def patch(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        permisos_antes = set(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        # partial=True permite update parcial
        serializer = RolSerializer(rol, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        permisos_despues = set(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        agregados = sorted(permisos_despues - permisos_antes)
        removidos = sorted(permisos_antes - permisos_despues)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='roles',
            descripcion=(
                f'Rol actualizado: ID={pk}, nombre={rol.nombre}. '
                f'Permisos agregados: {agregados or "ninguno"}. '
                f'Permisos removidos: {removidos or "ninguno"}'
            ),
        )
        return Response(serializer.data)

    # DELETE /api/roles/{id}/ - Eliminar un rol
    # Elimina el rol solo si no tiene usuarios activos asignados (BE-05).
    # Si tiene usuarios activos, retorna 409 con la cantidad afectada.
    # ATENCIÓN: También se eliminan los RolPermiso relacionados (CASCADE)
    def delete(self, request, pk):
        rol = self._get_object(pk)
        if rol is None:
            return Response({'detail': 'Rol no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        # Verifica si hay usuarios activos asignados a este rol
        usuarios_activos = UsuarioRol.objects.filter(rol=rol, usuario__estado='activo').count()
        if usuarios_activos > 0:
            return Response(
                {'detail': f'No se puede eliminar el rol porque tiene {usuarios_activos} usuario(s) activo(s) asignado(s).'},
                status=status.HTTP_409_CONFLICT,
            )
        # Guarda nombre y permisos antes de eliminar (para la bitácora)
        nombre = rol.nombre
        codigos_que_tenia = sorted(
            RolPermiso.objects.filter(rol=rol).values_list('permiso__codigo', flat=True)
        )
        # Elimina el rol (y sus RolPermiso por cascade)
        rol.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='roles',
            descripcion=(
                f'Rol eliminado: ID={pk}, nombre={nombre}. '
                f'Permisos que tenía: {codigos_que_tenia or "ninguno"}'
            ),
        )
        # Retorna 204 No Content (sin cuerpo de respuesta)
        return Response(status=status.HTTP_204_NO_CONTENT)



# PERMISO LIST CREATE VIEW - CRUD de Permisos
# Endpoints para Permisos: GET y POST
#
# - GET  /api/roles/permisos/  -> Lista todos los permisos
# - POST /api/roles/permisos/  -> Crea un nuevo permiso
#
# Un permiso representa una acción que un rol puede tener.
# Ejemplos: "usuarios.ver", "usuarios.crear", "reportes.exportar"
class PermisoListCreateView(APIView):
    permission_classes = [EsAdministrador]

    # GET /api/roles/permisos/ - Lista todos los permisos
    def get(self, request):
        # Obtiene todos los permisos, ordenados por módulo y código
        permisos = Permiso.objects.all().order_by('modulo', 'codigo')
        serializer = PermisoSerializer(permisos, many=True)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='permisos',
            descripcion='Consulta de lista de permisos',
        )
        return Response(serializer.data)

    # POST /api/roles/permisos/ - Crea un nuevo permiso
    def post(self, request):
        serializer = PermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        permiso = serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='permisos',
            descripcion=f'Permiso creado: ID={permiso.id}, codigo={permiso.codigo}',
        )
        return Response(PermisoSerializer(permiso).data, status=status.HTTP_201_CREATED)



# PERMISO DETAIL VIEW - Ver/Actualizar/Eliminar un permiso específico
# Endpoints para un permiso específico: /api/roles/permisos/{id}/
# - GET    /api/roles/permisos/{id}/   -> Ver detalle
# - PUT    /api/roles/permisos/{id}/   -> Atualización completa
# - PATCH  /api/roles/permisos/{id}/   -> Atualización parcial
# - DELETE /api/roles/permisos/{id}/   -> Eliminar
class PermisoDetailView(APIView):
    permission_classes = [EsAdministrador]

    def _get_object(self, pk):
        try:
            return Permiso.objects.get(pk=pk)
        except Permiso.DoesNotExist:
            return None

    def get(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='permisos',
            descripcion=f'Consulta de permiso: ID={pk}',
        )
        return Response(PermisoSerializer(permiso).data)

    def put(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermisoSerializer(permiso, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='permisos',
            descripcion=f'Permiso actualizado: ID={pk}',
        )
        return Response(serializer.data)

    def patch(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermisoSerializer(permiso, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.UPDATE,
            modulo='permisos',
            descripcion=f'Permiso actualizado parcialmente: ID={pk}',
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        permiso = self._get_object(pk)
        if permiso is None:
            return Response({'detail': 'Permiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        codigo = permiso.codigo
        permiso.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='permisos',
            descripcion=f'Permiso eliminado: ID={pk}, codigo={codigo}',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ROL PERMISO LIST CREATE VIEW - Asignar permisos a roles
# Endpoints para la tabla intermedia (relación rol-permiso):
#
# - GET  /api/roles/rol-permiso/  -> Lista todas las asignaciones
# - POST /api/roles/rol-permiso/  -> Asigna un permiso a un rol
#
# Esta tabla representa qué permisos tiene cada rol.
# Un registro = "el rol X tiene el permiso Y"
#
class RolPermisoListCreateView(APIView):
    permission_classes = [EsAdministrador]

    # GET /api/roles/rol-permiso/ - Lista todas las asignaciones
    def get(self, request):
        # select_related carga los objetos relacionados en una sola consulta
        qs = RolPermiso.objects.select_related('rol', 'permiso').all()
        serializer = RolPermisoSerializer(qs, many=True)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='rol_permiso',
            descripcion='Consulta de lista de asignaciones rol-permiso',
        )
        return Response(serializer.data)

    # POST /api/roles/rol-permiso/ - Asigna un permiso a un rol
    def post(self, request):
        serializer = RolPermisoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rp = serializer.save()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.CREATE,
            modulo='rol_permiso',
            descripcion=f'Permiso asignado: rol={rp.rol.nombre}, permiso={rp.permiso.codigo}',
        )
        return Response(RolPermisoSerializer(rp).data, status=status.HTTP_201_CREATED)


# ROL PERMISO DETAIL VIEW - Ver/Eliminar una asignación específica
# Endpoints para una asignación específica: /api/roles/rol-permiso/{id}/
#
# - GET    /api/roles/rol-permiso/{id}/   -> Ver detalle de una asignación
# - DELETE /api/roles/rol-permiso/{id}/   -> Quita el permiso del rol
class RolPermisoDetailView(APIView):
    permission_classes = [EsAdministrador]

    def _get_object(self, pk):
        try:
            return RolPermiso.objects.select_related('rol', 'permiso').get(pk=pk)
        except RolPermiso.DoesNotExist:
            return None

    def get(self, request, pk):
        rp = self._get_object(pk)
        if rp is None:
            return Response({'detail': 'Asignación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='rol_permiso',
            descripcion=f'Consulta de asignación rol-permiso: ID={pk}',
        )
        return Response(RolPermisoSerializer(rp).data)

    def delete(self, request, pk):
        rp = self._get_object(pk)
        if rp is None:
            return Response({'detail': 'Asignación no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        descripcion = f'Permiso removido: rol={rp.rol.nombre}, permiso={rp.permiso.codigo}'
        rp.delete()
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.DELETE,
            modulo='rol_permiso',
            descripcion=descripcion,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# HU-003. BE-07: GET /api/permisos/ - Listar todos los permisos agrupados por módulo
# Retorna un objeto donde cada clave es un módulo y su valor es la lista de permisos.
# Usado por el formulario de asignación de permisos a roles.
class PermisosAgrupadosView(APIView):
    permission_classes = [EsAdministrador]

    def get(self, request):
        permisos = Permiso.objects.all().order_by('modulo', 'codigo')
        serializer = PermisoSerializer(permisos, many=True)

        agrupados = defaultdict(list)
        for item in serializer.data:
            agrupados[item['modulo']].append(item)

        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='permisos',
            descripcion='Consulta de permisos agrupados por módulo',
        )
        return Response(dict(agrupados))