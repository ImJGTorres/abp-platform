from django.core.cache import cache

CACHE_KEY_TODOS = 'parametros_sistema_all'
CACHE_TIMEOUT = 900


def get_parametros_cacheados():
    return cache.get(CACHE_KEY_TODOS)


def set_parametros_cacheados(data):
    cache.set(CACHE_KEY_TODOS, data, CACHE_TIMEOUT)


def get_parametro(clave):
    cache_key = f'parametro_{clave}'
    return cache.get(cache_key)


def set_parametro(clave, data):
    cache_key = f'parametro_{clave}'
    cache.set(cache_key, data, CACHE_TIMEOUT)


def invalidar_cache_parametros():
    cache.delete(CACHE_KEY_TODOS)