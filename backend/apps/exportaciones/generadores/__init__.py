def _criterio_rojo(datos):
    """Texto del criterio de riesgo crítico (rojo) del semáforo RF34."""
    u = datos.get('umbrales_semaforo') or {}
    nota = u.get('nota_rojo', datos.get('umbral_bajo_rendimiento', 3.0))
    pct = u.get('pct_rojo', 50.0)
    return f"Riesgo crítico (rojo): nota < {nota:g} o actividades incumplidas >= {pct:g}%"
