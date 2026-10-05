"""
Semáforo académico RF34 (HU-029).

ponytail: stub de G5-1 hasta que llegue N5-1 (Nicole); al hacer merge se
conserva la versión de N5-1, que debe mantener estas mismas firmas.
"""
from decimal import Decimal

from .services import _get_parametro

NIVELES_SEMAFORO = ('verde', 'amarillo', 'rojo')


def obtener_umbrales():
    return {
        'nota_rojo': float(_get_parametro('umbral_nota_bajo_rendimiento', Decimal('3.0'))),
        'pct_rojo': float(_get_parametro('umbral_porcentaje_actividades_incumplidas', 50)),
        'nota_amarillo': float(_get_parametro('umbral_nota_alerta', Decimal('3.5'))),
        'pct_amarillo': float(_get_parametro('umbral_porcentaje_alerta', 25)),
    }


def clasificar_semaforo(nota, pct_incumplidas, tiene_actividades=True, umbrales=None):
    """
    Regla RF34:
    - rojo:     nota < 3.0 o % incumplidas >= 50
    - amarillo: nota < 3.5 o % incumplidas >= 25 (y no es rojo)
    - verde:    ninguna de las anteriores, o sin actividades asignadas
    Umbrales configurables en ParametroSistema.
    """
    if not tiene_actividades:
        return 'verde'
    u = umbrales or obtener_umbrales()
    if nota < u['nota_rojo'] or pct_incumplidas >= u['pct_rojo']:
        return 'rojo'
    if nota < u['nota_amarillo'] or pct_incumplidas >= u['pct_amarillo']:
        return 'amarillo'
    return 'verde'
