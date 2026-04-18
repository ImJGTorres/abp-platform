from django.apps import AppConfig


class BitacoraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bitacora'

    def ready(self):
        # Inicializa las señales de Django para auditar cambios en los modelos
        from apps.bitacora.signals import setup_signals
        setup_signals()