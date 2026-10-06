from .models import IdentidadInstitucional


def obtener_identidad():
    """
    Identidad institucional para PDF, Excel y correos.

    Retorna:
      nombre_institucion -- str
      programa_academico -- str
      logotipo_path      -- ruta absoluta del logotipo en disco, o None si no hay
                            logotipo, el archivo no existe o el storage no es local.
      logotipo_url       -- URL pública del logotipo, o None.
    """
    identidad = IdentidadInstitucional.obtener()

    logotipo_path = None
    logotipo_url = None
    if identidad.logotipo:
        logotipo_url = identidad.logotipo.url
        try:
            if identidad.logotipo.storage.exists(identidad.logotipo.name):
                logotipo_path = identidad.logotipo.path
        except NotImplementedError:
            # Storage remoto (p. ej. S3): no hay ruta en disco.
            pass

    return {
        'nombre_institucion': identidad.nombre_institucion,
        'programa_academico': identidad.programa_academico,
        'logotipo_path': logotipo_path,
        'logotipo_url': logotipo_url,
    }
