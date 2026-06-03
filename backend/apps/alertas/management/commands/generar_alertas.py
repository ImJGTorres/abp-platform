from django.core.management.base import BaseCommand
from apps.alertas.services import ejecutar_generacion_completa


class Command(BaseCommand):
    help = 'Genera alertas automáticas por actividades vencidas y entregables pendientes'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando generación de alertas...')
        resultados = ejecutar_generacion_completa()
        self.stdout.write(self.style.SUCCESS(
            f'Alertas generadas: {resultados}'
        ))
