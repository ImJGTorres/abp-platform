"""Lectura acotada de archivos .xlsx subidos por el usuario (cargas masivas).

Límites: tamaño del archivo, tamaño descomprimido (contra bombas zip) y cantidad de filas.
Se lee en modo read_only (en streaming), sin cargar todo el libro en memoria.
"""
import zipfile

from openpyxl import load_workbook

MAX_BYTES = 2 * 1024 * 1024            # 2 MB subidos
MAX_BYTES_DESCOMPRIMIDO = 50 * 1024 * 1024
MAX_FILAS = 2000


class ExcelInvalido(Exception):
    """El archivo no cumple los límites; el mensaje es apto para mostrarlo al usuario."""


def abrir_hoja(archivo):
    """Valida el archivo subido y devuelve su hoja activa (read_only)."""
    if archivo.size > MAX_BYTES:
        raise ExcelInvalido('El archivo supera el tamaño máximo de 2 MB.')
    try:
        with zipfile.ZipFile(archivo) as z:
            if sum(i.file_size for i in z.infolist()) > MAX_BYTES_DESCOMPRIMIDO:
                raise ExcelInvalido('El archivo es demasiado grande una vez descomprimido.')
    except zipfile.BadZipFile:
        raise ExcelInvalido('El archivo no es un .xlsx válido.')
    finally:
        archivo.seek(0)
    return load_workbook(archivo, read_only=True, data_only=True).active


def leer_filas(hoja, min_row=1):
    """Lista de filas (tuplas de valores); falla si hay más de MAX_FILAS."""
    filas = []
    for fila in hoja.iter_rows(min_row=min_row, values_only=True):
        filas.append(fila)
        if len(filas) > MAX_FILAS:
            raise ExcelInvalido(f'El archivo supera el máximo de {MAX_FILAS} filas.')
    return filas
