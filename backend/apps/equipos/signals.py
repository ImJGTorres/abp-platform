from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MiembroEquipo
from .servicios import liberar_actividades_de_miembro


@receiver(post_save, sender=MiembroEquipo)
def liberar_actividades_al_retirar(sender, instance, **kwargs):
    """Al retirar a un miembro, sus actividades del equipo quedan sin responsable."""
    if instance.estado == 'retirado':
        liberar_actividades_de_miembro(instance.equipo, instance.usuario_id)
