import logging

from django.db import transaction

logger = logging.getLogger(__name__)


def _destinatarios(anuncio):
    """
    IDs de usuario que reciben el anuncio (sin el autor):
    miembros activos de los equipos del proyecto, o, si el anuncio es solo de curso,
    estudiantes inscritos activos en el curso.
    """
    from apps.cursos.models import CursoEstudiante
    from apps.equipos.models import MiembroEquipo

    if anuncio.id_proyecto_id:
        ids = MiembroEquipo.objects.filter(
            equipo__proyecto_id=anuncio.id_proyecto_id,
            estado='activo',
        ).values_list('usuario_id', flat=True)
    else:
        ids = CursoEstudiante.objects.filter(
            curso_id=anuncio.id_curso_id,
            estado='activo',
        ).values_list('estudiante_id', flat=True)

    return sorted(set(ids) - {anuncio.id_autor_id})


def publicar_anuncio(autor, datos, request):
    """
    Guarda el anuncio, encola un correo 'anuncio' por cada integrante y registra en bitácora.
    `datos` son los validated_data de AnuncioSerializer. Retorna el Anuncio creado.
    """
    from apps.alertas.services import encolar_correo
    from apps.anuncios.models import Anuncio
    from apps.bitacora.models import BitacoraSistema
    from apps.bitacora.utils import registrar_evento

    with transaction.atomic():
        anuncio = Anuncio.objects.create(id_autor=autor, **datos)
        destinatarios = _destinatarios(anuncio)
        contexto = {
            'anuncio_id': anuncio.id,
            'titulo': anuncio.titulo,
            'mensaje': anuncio.mensaje,
            'curso_id': anuncio.id_curso_id,
            'proyecto_id': anuncio.id_proyecto_id,
            'autor': f'{autor.nombre} {autor.apellido}',
        }
        for usuario_id in destinatarios:
            encolar_correo(usuario_id, f'Nuevo anuncio: {anuncio.titulo}', 'anuncio', contexto)

    registrar_evento(
        request,
        BitacoraSistema.Accion.CREATE,
        'anuncios',
        f'Anuncio publicado: ID={anuncio.id}, curso={anuncio.id_curso_id}, '
        f'proyecto={anuncio.id_proyecto_id}, correos encolados={len(destinatarios)}',
    )
    return anuncio
