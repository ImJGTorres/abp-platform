from apps.bitacora.utils import registrar_evento
from apps.cursos.models import Actividad


def liberar_actividades_de_miembro(equipo, usuario_id, request=None):
    """Deja sin responsable las actividades del equipo que tenía asignadas el usuario.

    Deja rastro en bitácora (acción 'actividad_sin_responsable') por cada actividad
    liberada. Devuelve la cantidad de actividades liberadas.
    """
    actividades = list(
        Actividad.objects.filter(id_equipo_asignado=equipo).filter(
            id_responsable_id=usuario_id
        ) | Actividad.objects.filter(id_equipo_asignado=equipo, responsables=usuario_id)
    )
    for actividad in set(actividades):
        if actividad.id_responsable_id == usuario_id:
            actividad.id_responsable = None
            actividad.save(update_fields=['id_responsable'])
        actividad.responsables.remove(usuario_id)
        registrar_evento(
            request=request,
            accion='actividad_sin_responsable',
            modulo='equipos',
            descripcion=(
                f"Actividad '{actividad.nombre}' (id={actividad.id}) quedó sin responsable "
                f"al retirar al usuario {usuario_id} del equipo {equipo.id}."
            ),
        )
    return len(set(actividades))
