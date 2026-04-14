from collections import defaultdict
# defaultdict: Dict que permite crear valores por defecto para claves inexistentes
# Se usa para agrupar parámetros por categoría fácilmente

from django.core.exceptions import ValidationError
# ValidationError: Excepción de Django para errores de validación en modelos

from rest_framework import status
# status: Constantes de códigos HTTP (HTTP_200_OK, HTTP_404_NOT_FOUND, etc.)

from rest_framework.response import Response
# Response: Objeto de Django REST Framework para retornar respuestas JSON

from rest_framework.views import APIView
# APIView: Clase base de DRF para crear vistas basadas en clases

from apps.bitacora.models import BitacoraSistema
# BitacoraSistema: Modelo para registrar eventos del sistema (auditoría)

from apps.bitacora.utils import registrar_evento
# registrar_evento: Función utilitaria para crear registros en la bitácora

from .cache import get_parametros_cacheados, set_parametros_cacheados, invalidar_cache_parametros
# Funciones de gestión del caché de parámetros:
# - get_parametros_cacheados(): Obtiene datos cacheados si existen
# - set_parametros_cacheados(): Guarda datos en caché
# - invalidar_cache_parametros(): Elimina el caché después de una actualización

from .models import ParametroSistema
# ParametroSistema: Modelo de parámetros de configuración

from .permissions import EsAdministrador
# EsAdministrador: Permiso personalizado que requiere rol de administrador

from .serializers import ParametroSistemaSerializer
# ParametroSistemaSerializer: Serializador para convertir modelos a JSON


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
