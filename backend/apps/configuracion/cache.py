from django.core.cache import cache
# cache: Interfaz de Django para acceder al sistema de caché configurado
# Permite almacenar y recuperar datos temporalmente en memoria

# =============================================================================
# CONSTANTES DE CONFIGURACIÓN DEL CACHÉ
# =============================================================================

# Clave única para almacenar todos los parámetros del sistema en caché
# Se usa en get_parametros_cacheados() y set_parametros_cacheados()
CACHE_KEY_TODOS = 'parametros_sistema_all'

# Timeout en segundos (900 segundos = 15 minutos)
# Tiempo máximo que los datos permanecerán en caché antes de expirar
# Pasado este tiempo, la próxima consultairá a la base de datos
CACHE_TIMEOUT = 900


# =============================================================================
# FUNCIONES PARA GESTIÓN DEL CACHÉ DE PARÁMETROS
# =============================================================================

def get_parametros_cacheados():
    """
    Obtiene todos los parámetros del sistema desde el caché.
    
    Returns:
        dict or None: Diccionario con los parámetros agrupados por categoría
                      si existen en caché, None si no hay caché válido.
    
    Uso:
        Se llama al inicio del método GET de ConfiguracionView.
        Si retorna datos, se evita consultar la base de datos.
    """
    return cache.get(CACHE_KEY_TODOS)


def set_parametros_cacheados(data):
    """
    Guarda todos los parámetros del sistema en el caché.
    
    Args:
        data: Diccionario con los parámetros agrupados por categoría
              (resultado de transformar QuerySet a formato JSON)
    
    Uso:
        Se llama después de obtener datos de la base de datos
        para evitar consultas repetidas en próximas solicitudes.
        Los datos se almacenan por 15 minutos (CACHE_TIMEOUT).
    """
    cache.set(CACHE_KEY_TODOS, data, CACHE_TIMEOUT)


def get_parametro(clave):
    """
    Obtiene un parámetro específico del caché por su clave.
    
    Args:
        clave: Clave única del parámetro (ej: 'max_estudiantes_por_equipo')
    
    Returns:
        dict or None: Datos del parámetro si existe en caché, None si no.
    
    Nota:
        Esta función está definida pero no se usa actualmente.
        Podría utilizarse para obtener un solo parámetro sin caché global.
    """
    cache_key = f'parametro_{clave}'
    return cache.get(cache_key)


def set_parametro(clave, data):
    """
    Guarda un parámetro específico en el caché.
    
    Args:
        clave: Clave única del parámetro
        data: Datos del parámetro a guardar
    
    Nota:
        Esta función está definida pero no se usa actualmente.
        Podría utilizarse para actualizar un solo parámetro en caché.
    """
    cache_key = f'parametro_{clave}'
    cache.set(cache_key, data, CACHE_TIMEOUT)


def invalidar_cache_parametros():
    """
    Invalida (elimina) el caché de todos los parámetros del sistema.
    
    Uso:
        Se llama después de actualizar un parámetro (PATCH exitoso).
        Esto asegura que la próxima consulta obtenga los datos actualizados
        desde la base de datos en lugar de devolver datos obsoletos.
        
    Nota:
        Solo elimina el caché de todos los parámetros (CACHE_KEY_TODOS).
        No elimina los caché individuales de parámetros específicos.
    """
    cache.delete(CACHE_KEY_TODOS)