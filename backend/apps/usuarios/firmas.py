"""Firmas (bytes mágicos) de los formatos de archivo permitidos.

Una extensión o un Content-Type los escribe el cliente; los primeros bytes del contenido no
se pueden cambiar sin romper el archivo. Se usa para no aceptar, por ejemplo, un .html
renombrado a .png.
"""

IMAGENES = {
    'jpg': (b'\xff\xd8\xff',),
    'jpeg': (b'\xff\xd8\xff',),
    'png': (b'\x89PNG\r\n\x1a\n',),
    'gif': (b'GIF87a', b'GIF89a'),
}
DOCUMENTOS = {
    'pdf': (b'%PDF-',),
    'docx': (b'PK\x03\x04',),   # contenedor zip (Office Open XML)
    'xlsx': (b'PK\x03\x04',),
}


def _empieza_con(cabecera, firmas):
    return any(cabecera.startswith(f) for f in firmas)


def extension_de_imagen(cabecera):
    """Extensión según el contenido ('jpg', 'png', 'gif', 'webp') o None si no es una imagen permitida."""
    for ext in ('jpg', 'png', 'gif'):
        if _empieza_con(cabecera, IMAGENES[ext]):
            return ext
    if cabecera[:4] == b'RIFF' and cabecera[8:12] == b'WEBP':
        return 'webp'
    return None


def contenido_coincide(extension, cabecera):
    """True si la cabecera del archivo corresponde a la extensión declarada."""
    firmas = IMAGENES.get(extension) or DOCUMENTOS.get(extension)
    return bool(firmas) and _empieza_con(cabecera, firmas)
