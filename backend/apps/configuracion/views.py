from collections import defaultdict
# defaultdict: Dict que permite crear valores por defecto para claves inexistentes
# Se usa para agrupar parámetros por categoría fácilmente

from django.core.exceptions import ValidationError
# ValidationError: Excepción de Django para errores de validación en modelos

from django.db import transaction, models
# transaction: Proporciona atomic() para transacciones de base de datos
# models: Módulo de Django para consultas avanzadas (Count)

from rest_framework import status, viewsets
# status: Constantes de códigos HTTP (HTTP_200_OK, HTTP_404_NOT_FOUND, etc.)
# viewsets: Clase base para crear ViewSets en DRF

from rest_framework.response import Response
# Response: Objeto de Django REST Framework para retornar respuestas JSON

from rest_framework.views import APIView
# APIView: Clase base de DRF para crear vistas basadas en clases

from rest_framework.permissions import IsAdminUser
# IsAdminUser: Permiso de DRF que requiere is_staff=True

from apps.bitacora.models import BitacoraSistema
# BitacoraSistema: Modelo para registrar eventos del sistema (auditoría)

from apps.bitacora.utils import registrar_evento
# registrar_evento: Función utilitaria para crear registros en la bitácora

from .cache import get_parametros_cacheados, set_parametros_cacheados, invalidar_cache_parametros
# Funciones de gestión del caché de parámetros:
# - get_parametros_cacheados(): Obtiene datos cacheados si existen
# - set_parametros_cacheados(): Guarda datos en caché
# - invalidar_cache_parametros(): Elimina el caché después de una actualización

from .models import ParametroSistema, PeriodoAcademico
from .permissions import EsAdministrador, IsAdminOrDocente
from .serializers import ParametroSistemaSerializer, PeriodoAcademicoSerializer
from apps.cursos.models import Curso
# ParametroSistemaSerializer: Serializador para convertir modelos a JSON
# PeriodoAcademicoSerializer: Serializador para períodos académicos


class ConfiguracionView(APIView):
    """
    Vista principal para gestionar los parámetros de configuración del sistema.
    
    Proporciona dos endpoints:
    1. GET /api/configuracion/ - Lista todos los parámetros agrupados por categoría
    2. PATCH /api/configuracion/<clave>/ - Actualiza un parámetro específico
    
    Ambas operaciones requieren rol de administrador (configurado en permission_classes).
    
    El caché se utiliza para mejorar rendimiento:
    - GET consulta caché primero, si no existe consulta BD y cachea el resultado
    - PATCH invalida el caché después de una actualización exitosa
    """
    
    # permission_classes: Define qué permisos requiere esta vista
    # Solo usuarios con rol 'administrador' pueden acceder
    permission_classes = [EsAdministrador]

    def get(self, request):
        """
        Lista todos los parámetros de configuración del sistema.
        
        Retorna los parámetros agrupados por categoría:
        - institucional: Parámetros de la institución
        - seguridad: Parámetros de seguridad
        - archivos: Parámetros relacionados con archivos
        - sesiones: Parámetros de gestión de sesiones
        - general: Parámetros generales
        
        Cada parámetro incluye: clave, valor, valor_casteado, descripcion, tipo_dato, fecha_actualizacion.
        
        Flujo:
        1. Verifica si hay datos en caché
        2. Si hay caché, retorna los datos (evita consulta a BD)
        3. Si no hay caché, consulta la BD
        4. Agrupa los parámetros por categoría
        5. Guarda el resultado en caché para próximas solicitudes
        6. Registra la consulta en la bitácora
        
        Returns:
            Response: Diccionario JSON con parámetros agrupados por categoría
        """
        # Paso 1: Verificar si existen datos en caché
        # El caché store los parámetros por 15 minutos para evitar consultas repetidas a la BD
        cached_data = get_parametros_cacheados()
        
        if cached_data is not None:
            # El caché tiene datos válidos, retornarlos directamente
            # Registrar en bitácora que la consulta vino del caché
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.ACCESS,
                modulo='configuracion',
                descripcion='Consulta de parámetros del sistema (desde caché)',
            )
            return Response(cached_data)

        # Paso 2: No hay caché, consultar la base de datos
        # Obtiene todos los parámetros del sistema
        parametros = ParametroSistema.objects.all()
        
        # Serializa los objetos del modelo a formato JSON
        serializer = ParametroSistemaSerializer(parametros, many=True)

        # Paso 3: Agrupar parámetros por categoría
        # Crea un diccionario donde cada clave es una categoría
        # y el valor es una lista de parámetros de esa categoría
        agrupados = defaultdict(list)
        
        for item in serializer.data:
            # Para cada parámetro, crea un diccionario con los campos relevantes
            # Se excluye 'categoria' porque ya es la clave del grupo
            agrupados[item['categoria']].append({
                'clave':              item['clave'],
                'valor':              item['valor'],
                'valor_casteado':     item['valor_casteado'],
                'descripcion':        item['descripcion'],
                'tipo_dato':          item['tipo_dato'],
                'fecha_actualizacion': item['fecha_actualizacion'],
            })

        # Convierte el defaultdict a dict normal para la respuesta
        result = dict(agrupados)
        
        # Paso 4: Guardar en caché para futuras solicitudes
        # Se cachea por 15 minutos (CACHE_TIMEOUT = 900)
        set_parametros_cacheados(result)

        # Paso 5: Registrar la consulta en bitácora
        registrar_evento(
            request,
            accion=BitacoraSistema.Accion.ACCESS,
            modulo='configuracion',
            descripcion='Consulta de parámetros del sistema',
        )
        
        # Retorna los parámetros agrupados por categoría
        return Response(result)

    def patch(self, request, clave):
        """
        Actualiza el valor de un parámetro específico del sistema.
        
        Args:
            request: Objeto HTTP request de DRF
            clave: Clave del parámetro a actualizar (parte de la URL)
        
        Cuerpo de la solicitud (JSON):
            {
                "valor": "nuevo_valor",  // Required
                "rango": {"min": 1, "max": 10}  // Opcional, solo para integers
            }
        
        Flujo:
        1. Busca el parámetro por su clave en la BD
        2. Valida que el parámetro exista (404 si no)
        3. Valida que se proporcione el campo "valor" (400 si no)
        4. Valida el tipo de dato (para integers verifica que sea numérico)
        5. Valida el rango si se proporciona (para integers)
        6. Guarda el nuevo valor
        7. Invalida el caché (próxima consultairá a la BD)
        8. Registra la actualización en bitácora
        
        Returns:
            Response: Datos del parámetro actualizado (200)
            Response: Error 404 si no existe el parámetro
            Response: Error 400 si la validación falla
        """
        
        # Paso 1: Buscar el parámetro por su clave
        try:
            parametro = ParametroSistema.objects.get(clave=clave)
        except ParametroSistema.DoesNotExist:
            # El parámetro no existe, retornar error 404
            return Response(
                {'detail': f'Parámetro "{clave}" no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Paso 2: Validar que se proporcione el campo "valor"
        nuevo_valor = request.data.get('valor')
        if nuevo_valor is None:
            return Response(
                {'detail': 'El campo "valor" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Paso 3: Validar rango para parámetros de tipo INTEGER
        # Si el parámetro es entero, puede tener restricciones de rango (min/max)
        rango = request.data.get('rango')
        
        if parametro.tipo_dato == ParametroSistema.TipoDato.INTEGER and rango:
            # Verificar que el valor sea un número entero válido
            try:
                valor_int = int(nuevo_valor)
            except ValueError:
                return Response(
                    {'detail': f'Valor debe ser entero, recibido: "{nuevo_valor}"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar rango mínimo si se especifica
            if 'min' in rango and valor_int < rango['min']:
                return Response(
                    {'detail': f'Valor mínimo permitido: {rango["min"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar rango máximo si se especifica
            if 'max' in rango and valor_int > rango['max']:
                return Response(
                    {'detail': f'Valor máximo permitido: {rango["max"]}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Paso 4: Actualizar el valor del parámetro
        # Capturar el valor anterior ANTES de modificar (para bitácora)
        valor_anterior = parametro.valor
        # Convertir a string para almacenar en el campo TextField
        parametro.valor = str(nuevo_valor)
        
        # Registrar el usuario que realizó la modificación (para auditoría)
        parametro.usuario_modifico = request.user

        # Paso 5: Guardar con validación completa
        # full_clean() ejecuta las validaciones del modelo (clean())
        # Si falla, retorna error 400 con los mensajes de validación
        try:
            parametro.full_clean()
            parametro.save()
            
            # Invalida el caché para que la próxima consulta obtenga datos actualizados
            # Esto es crítico para que los cambios se reflejen inmediatamente
            invalidar_cache_parametros()
            
            # Registrar en bitácora solo si el valor realmente cambió
            if valor_anterior != parametro.valor:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.UPDATE,
                    modulo='configuracion',
                    descripcion=f"Parámetro '{parametro.clave}' actualizado: '{valor_anterior}' → '{parametro.valor}'"
                )
            
        except ValidationError as e:
            # Error de validación (tipo de dato incorrecto, formato inválido, etc.)
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        # Paso 6: Serializar y retornar el parámetro actualizado
        serializer = ParametroSistemaSerializer(parametro)
        
        return Response(serializer.data)


class PeriodoAcademicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar períodos académicos.
    
    Proporciona los endpoints:
    - GET /api/periodos/ - Lista todos los períodos ordenados por fecha_inicio descendente
    - POST /api/periodos/ - Crea un nuevo período académico
    - PUT /api/periodos/<id>/ - Actualiza un período académico (solo admin)
    - PATCH /api/periodos/<id>/ - Actualiza parcialmente un período académico (solo admin)
    - DELETE /api/periodos/<id>/ - Elimina un período académico (solo admin)
    
    El endpoint GET permite acceso a administradores y docentes (IsAdminOrDocente).
    Los endpoints POST, PUT, PATCH y DELETE solo permiten acceso a administradores (IsAdminUser).
    
    Cada período incluye el conteo de cursos asociados en el campo total_cursos.
    """
    
    serializer_class = PeriodoAcademicoSerializer
    
    def get_queryset(self):
        queryset = PeriodoAcademico.objects.annotate(
            total_cursos=models.Count('curso')
        ).order_by('-fecha_inicio')
        return queryset
    
    def get_permissions(self):
        # Los permisos para update, partial_update y destroy requieren ser administrador (is_staff)
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrador()]
        return [IsAdminOrDocente()]
    
    def perform_create(self, serializer):
        serializer.save(usuario_creo=self.request.user)
    
    # Método auxiliar para verificar si hay proyectos activos en los cursos del período
    # Se usa para validar si se pueden modificar las fechas (retorna True si hay proyectos en_curso)
    def _has_active_projects(self, periodo):
        from django.apps import apps
        try:
            # Intenta obtener el modelo Proyecto de la app proyectos
            # Si la app no existe, retorna False (no hay restricción)
            Proyecto = apps.get_model('proyectos', 'Proyecto')
            cursos = Curso.objects.filter(id_periodo_academico=periodo)
            for curso in cursos:
                if hasattr(curso, 'proyecto') and curso.proyecto.estado == 'en_curso':
                    return True
        except ImportError:
            pass
        return False
    
    # Método auxiliar para contar proyectos activos en los cursos del período
    # Retorna el conteo de proyectos con estado 'en_curso' para mostrar en el error 409
    def _get_active_projects_count(self, periodo):
        from django.apps import apps
        try:
            Proyecto = apps.get_model('proyectos', 'Proyecto')
            return Proyecto.objects.filter(curso__id_periodo_academico=periodo, estado='en_curso').count()
        except ImportError:
            return 0
    
    def create(self, request, *args, **kwargs):
        # Si el estado del nuevo período es 'activo', se deben inactivar los demás períodos activos
        # Esto se hace en una transacción atómica para garantir consistencia
        estado = request.data.get('estado')
        
        if estado == PeriodoAcademico.Estado.ACTIVO:
            with transaction.atomic():
                # Actualiza todos los períodos activos a inactivo antes de crear el nuevo
                PeriodoAcademico.objects.filter(
                    estado=PeriodoAcademico.Estado.ACTIVO
                ).update(estado=PeriodoAcademico.Estado.INACTIVO)
                
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                
                # Registro en bitácora de la creación del período académico
                # Si falla el registro, no se interrumpe la operación principal (try/except)
                try:
                    registrar_evento(
                        request,
                        accion=BitacoraSistema.Accion.CREATE,
                        modulo='periodos_academicos',
                        descripcion=f"Período académico creado: {serializer.instance.nombre}"
                    )
                except Exception:
                    pass
                
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
        else:
            return super().create(request, *args, **kwargs)
    
# Endpoint PUT/PATCH para actualizar un período académico
    # - PUT: actualización completa (reemplazo total)
    # - PATCH: actualización parcial
    #URL: /api/periodos/<id>/
    def update(self, request, *args, **kwargs):
        # Se capturan los valores antes del update para registrar en bitácora
        # Esto permite auditoría de los cambios realizados
        instance = self.get_object()
        valores_anteriores = {
            'nombre': instance.nombre,
            'fecha_inicio': str(instance.fecha_inicio),
            'fecha_fin': str(instance.fecha_fin),
            'estado': instance.estado,
        }
        
        # partial=True indica que es un PATCH (actualización parcial), False es PUT
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Se extraen los nuevos valores validados para verificar reglas de negocio
        nuevo_estado = serializer.validated_data.get('estado')
        nueva_fecha_inicio = serializer.validated_data.get('fecha_inicio')
        nueva_fecha_fin = serializer.validated_data.get('fecha_fin')
        
        # force_update permite modificar fechas aunque haya proyectos activos
        # Es un flag de emergencia para casos donde se necesite forzar el cambio
        force_update = request.data.get('force_update', False)
        
        # Verificar si las fechas fueron modificadas
        fecha_cambio = (nueva_fecha_inicio and nueva_fecha_inicio != instance.fecha_inicio) or \
                       (nueva_fecha_fin and nueva_fecha_fin != instance.fecha_fin)
        
        # Si las fechas cambian y hay proyectos activos, retorna 409 Conflict
        # Excepto si force_update=true (permite forzar el cambio)
        if fecha_cambio and not force_update:
            proyectos_activos = self._get_active_projects_count(instance)
            if proyectos_activos > 0:
                return Response(
                    {'error': 'No se pueden modificar las fechas', 'proyectos_activos': proyectos_activos},
                    status=status.HTTP_409_CONFLICT
                )
        
        # Si el nuevo estado es 'activo' y el actual no lo era,
        # se deben inactivar los demás períodos activos (solo puede haber uno activo)
        if nuevo_estado == PeriodoAcademico.Estado.ACTIVO and instance.estado != PeriodoAcademico.Estado.ACTIVO:
            with transaction.atomic():
                # Excluye el período actual para no self-actualizarse
                PeriodoAcademico.objects.filter(
                    estado=PeriodoAcademico.Estado.ACTIVO
                ).exclude(pk=instance.pk).update(estado=PeriodoAcademico.Estado.INACTIVO)
                
                self.perform_update(serializer)
                
                # Registro en bitácora de la actualización del período
                valores_nuevos = {
                    'nombre': serializer.instance.nombre,
                    'fecha_inicio': str(serializer.instance.fecha_inicio),
                    'fecha_fin': str(serializer.instance.fecha_fin),
                    'estado': serializer.instance.estado,
                }
                
                try:
                    registrar_evento(
                        request,
                        accion=BitacoraSistema.Accion.UPDATE,
                        modulo='periodos_academicos',
                        descripcion=f"Período académico actualizado: {serializer.instance.nombre}"
                    )
                except Exception:
                    pass
                
                return Response(serializer.data)
        else:
            # Actualización normal (sin cambio de estado a activo)
            self.perform_update(serializer)
            
            # Registro en bitácora de la actualización del período
            valores_nuevos = {
                'nombre': serializer.instance.nombre,
                'fecha_inicio': str(serializer.instance.fecha_inicio),
                'fecha_fin': str(serializer.instance.fecha_fin),
                'estado': serializer.instance.estado,
            }
            
            try:
                registrar_evento(
                    request,
                    accion=BitacoraSistema.Accion.UPDATE,
                    modulo='periodos_academicos',
                    descripcion=f"Período académico actualizado: {serializer.instance.nombre}"
                )
            except Exception:
                pass
            
            return Response(serializer.data)
    
    # Endpoint PATCH para actualización parcial
    # Delegado al método update con partial=True
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    # Endpoint DELETE para eliminar un período académico
    #URL: /api/periodos/<id>/
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Verificar si hay cursos asociados al período
        # Si hay cursos, no se puede eliminar (retorna 409 Conflict)
        cursos_count = Curso.objects.filter(id_periodo_academico=instance).count()
        
        if cursos_count > 0:
            return Response(
                {'error': 'No se puede eliminar el periodo', 'cursos_afectados': cursos_count},
                status=status.HTTP_409_CONFLICT
            )
        
        # Se capturan los valores antes de eliminar para registrar en bitácora
        valores_anteriores = {
            'nombre': instance.nombre,
            'fecha_inicio': str(instance.fecha_inicio),
            'fecha_fin': str(instance.fecha_fin),
            'estado': instance.estado,
        }
        
        # Eliminar el período académico
        self.perform_destroy(instance)
        
        # Registro en bitácora de la eliminación del período
        try:
            registrar_evento(
                request,
                accion=BitacoraSistema.Accion.DELETE,
                modulo='periodos_academicos',
                descripcion=f"Período académico eliminado: {valores_anteriores['nombre']}"
            )
        except Exception:
            pass
        
        return Response(status=status.HTTP_204_NO_CONTENT)
