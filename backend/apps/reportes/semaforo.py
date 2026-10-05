from decimal import Decimal

VERDE = 'verde'
AMARILLO = 'amarillo'
ROJO = 'rojo'


def obtener_umbrales():
    """
    Lee los umbrales del semáforo desde ParametroSistema.
    Si un parámetro no existe se usa su valor por defecto.
    """
    from .services import _get_parametro

    return {
        'nota_rojo': _get_parametro('umbral_nota_bajo_rendimiento', Decimal('3.0')),
        'pct_rojo': _get_parametro('umbral_porcentaje_actividades_incumplidas', 50),
        'nota_amarillo': _get_parametro('umbral_nota_alerta', Decimal('3.5')),
        'pct_amarillo': _get_parametro('umbral_porcentaje_alerta', 25),
    }


def clasificar_semaforo(nota, pct_incumplidas, tiene_actividades=True, umbrales=None):
    """
    Clasifica el rendimiento de un estudiante en un semáforo de 3 niveles (RF34).

    Regla, evaluada en este orden:
      1. Sin actividades asignadas (tiene_actividades=False)  -> 'verde'.
      2. nota < umbral_nota_bajo_rendimiento (3.0)
         o pct_incumplidas >= umbral_porcentaje_actividades_incumplidas (50) -> 'rojo'.
      3. nota < umbral_nota_alerta (3.5)
         o pct_incumplidas >= umbral_porcentaje_alerta (25)                  -> 'amarillo'.
      4. En otro caso                                                        -> 'verde'.

    Los valores entre paréntesis son los usados por defecto; los reales se leen
    de ParametroSistema con obtener_umbrales().

    Parámetros:
      nota             -- nota promedio en escala 0-5.
      pct_incumplidas  -- % de actividades incumplidas (0-100).
      tiene_actividades -- False si el estudiante no tiene actividades asignadas.
      umbrales         -- dict de obtener_umbrales(); si es None se consulta la BD.
                          Pásalo al clasificar muchos estudiantes para no repetir
                          las consultas.

    Retorna 'verde', 'amarillo' o 'rojo'.
    Ejemplos: (2.8, 10) -> 'rojo', (3.2, 10) -> 'amarillo',
              (4.0, 10) -> 'verde', (4.0, 60) -> 'rojo'.
    """
    if not tiene_actividades:
        return VERDE

    if umbrales is None:
        umbrales = obtener_umbrales()

    nota = Decimal(str(nota))
    pct = Decimal(str(pct_incumplidas))

    if nota < umbrales['nota_rojo'] or pct >= umbrales['pct_rojo']:
        return ROJO
    if nota < umbrales['nota_amarillo'] or pct >= umbrales['pct_amarillo']:
        return AMARILLO
    return VERDE
