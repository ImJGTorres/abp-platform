from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Entregable, EntregableVersion


def _obtener_original(entregable):
    """Remonta la cadena id_version_anterior hasta el primer entregable del hilo."""
    actual = entregable
    while actual.id_version_anterior_id is not None:
        actual = actual.id_version_anterior
    return actual


def crear_nueva_version(entregable_rechazado, usuario, motivo=''):
    if entregable_rechazado.estado != 'rechazado':
        raise ValidationError('Solo se puede crear una nueva versión de un entregable rechazado.')

    with transaction.atomic():
        original = _obtener_original(entregable_rechazado)
        numero_version = entregable_rechazado.numero_version + 1

        nuevo = Entregable.objects.create(
            titulo=entregable_rechazado.titulo,
            descripcion=entregable_rechazado.descripcion,
            tipo=entregable_rechazado.tipo,
            id_actividad=entregable_rechazado.id_actividad,
            id_equipo=entregable_rechazado.id_equipo,
            estado='borrador',
            numero_version=numero_version,
            id_version_anterior=entregable_rechazado,
        )

        EntregableVersion.objects.create(
            id_entregable_original=original,
            id_version=nuevo,
            numero_version=numero_version,
            id_usuario=usuario,
            motivo_revision=motivo,
        )

        try:
            from apps.bitacora.models import BitacoraSistema
            BitacoraSistema.objects.create(
                id_usuario=usuario,
                nombre_usuario=f'{usuario.nombre} {usuario.apellido}',
                accion='CREAR_VERSION',
                modulo='entregables',
                descripcion=f'Nueva versión {numero_version} del entregable {entregable_rechazado.id}',
            )
        except Exception:
            pass

    return nuevo
