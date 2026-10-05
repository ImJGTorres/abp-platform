import logging

logger = logging.getLogger(__name__)

# Membrete por defecto si no hay identidad configurada (HU-035).
NOMBRE_INSTITUCION = "UFPS — Plataforma ABP"
PROGRAMA = "Ingeniería de Sistemas"


def _criterio_rojo(datos):
    """Texto del criterio de riesgo crítico (rojo) del semáforo RF34."""
    u = datos.get('umbrales_semaforo') or {}
    nota = u.get('nota_rojo', datos.get('umbral_bajo_rendimiento', 3.0))
    pct = u.get('pct_rojo', 50.0)
    return f"Riesgo crítico (rojo): nota < {nota:g} o actividades incumplidas >= {pct:g}%"


def _identidad():
    """(nombre, programa, logotipo_path) configurados; la exportación nunca falla por esto."""
    try:
        from apps.configuracion.identidad import obtener_identidad
        identidad = obtener_identidad()
    except Exception:
        logger.warning("No se pudo leer la identidad institucional; se usa la de por defecto",
                       exc_info=True)
        identidad = {}
    return (
        identidad.get('nombre_institucion') or NOMBRE_INSTITUCION,
        identidad.get('programa_academico') or PROGRAMA,
        identidad.get('logotipo_path'),
    )
