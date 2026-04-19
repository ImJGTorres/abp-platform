import logging

from django.db.models import signals
from django.apps import apps

from apps.bitacora.models import BitacoraSistema
from apps.bitacora.utils import registrar_evento


logger = logging.getLogger(__name__)


def get_model_name(model):
    """Obtiene el nombre del modelo en minúsculas para usar como módulo en la bitácora."""
    return model._meta.model_name.lower()


def _get_values_from_instance(instance):
    """Extrae los valores de los campos de una instancia del modelo para almacenar en la bitácora."""
    exclude_fields = {'_state', 'pk'}
    result = {}
    for field in instance._meta.fields:
        if field.name in exclude_fields:
            continue
        value = getattr(instance, field.name, None)
        if hasattr(value, 'id'):
            result[field.name] = value.id
        elif hasattr(value, '__class__') and hasattr(value, '__dict__'):
            result[field.name] = str(value)
        else:
            result[field.name] = value
    return result


def post_save_signal(sender, instance, created, **kwargs):
    """Signal que se ejecuta después de guardar un objeto. Registra en bitácora si fue creado o actualizado."""
    try:
        accion = BitacoraSistema.Accion.CREATE if created else BitacoraSistema.Accion.UPDATE
        modulo = get_model_name(sender)
        
        valores_nuevos = _get_values_from_instance(instance)
        
        valores_anteriores = None
        if not created:
            try:
                old_instance = sender.objects.get(pk=instance.pk)
                valores_anteriores = _get_values_from_instance(old_instance)
            except sender.DoesNotExist:
                pass
            descripcion = f'{modulo.capitalize()} actualizado (valores anteriores no disponibles)'
        else:
            descripcion = f'{modulo.capitalize()} creado'
        
        if valores_anteriores:
            descripcion = f'{modulo.capitalize()} actualizado'
        
        registrar_evento(
            request=None,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
        )
    except Exception as e:
        logger.error(f'Error en post_save de {sender._meta.label}: {e}')


def post_delete_signal(sender, instance, **kwargs):
    """Signal que se ejecuta después de eliminar un objeto. Registra en bitácora la eliminación."""
    try:
        modulo = get_model_name(sender)
        valores_anteriores = _get_values_from_instance(instance)
        
        registrar_evento(
            request=None,
            accion=BitacoraSistema.Accion.DELETE,
            modulo=modulo,
            descripcion=f'{modulo.capitalize()} eliminado',
        )
    except Exception as e:
        logger.error(f'Error en post_delete de {sender._meta.label}: {e}')


def setup_signals():
    """Conecta las señales post_save y post_delete a los modelos que se deben auditar."""
    models_to_track = []
    
    try:
        models_to_track.append(apps.get_model('usuarios', 'Usuario'))
    except LookupError:
        pass
    
    try:
        models_to_track.append(apps.get_model('roles', 'Rol'))
    except LookupError:
        pass
    
    try:
        models_to_track.append(apps.get_model('configuracion', 'PeriodoAcademico'))
    except LookupError:
        pass
    
    try:
        models_to_track.append(apps.get_model('cursos', 'Curso'))
    except LookupError:
        pass
    
    for model in models_to_track:
        signals.post_save.connect(post_save_signal, sender=model)
        signals.post_delete.connect(post_delete_signal, sender=model)