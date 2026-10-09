import logging
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.alertas.services import ejecutar_generacion_completa, generar_recordatorios_48h

logger = logging.getLogger(__name__)

# (nombre, función, intervalo en minutos). Otras HU solo agregan una línea.
TAREAS = [
    ('alertas', ejecutar_generacion_completa, 15),
    ('recordatorios', generar_recordatorios_48h, 1440),  # HU-040: diaria
]

# Tareas cuyo intervalo se puede cambiar en ParametroSistema.
PARAMETROS_INTERVALO = {'alertas': 'intervalo_alertas_minutos'}

PAUSA_SEGUNDOS = 60


def _intervalo_minutos(nombre, por_defecto):
    clave = PARAMETROS_INTERVALO.get(nombre)
    if not clave:
        return por_defecto
    from apps.reportes.services import _get_parametro
    try:
        return _get_parametro(clave, por_defecto)
    except Exception:
        logger.warning("Valor inválido en %s; se usa %s min", clave, por_defecto)
        return por_defecto


def correr_tareas(ultima, ahora, forzar=False):
    """Ejecuta las tareas cuyo intervalo ya se cumplió (o todas si forzar)."""
    for nombre, funcion, minutos in TAREAS:
        try:
            intervalo = _intervalo_minutos(nombre, minutos) * 60
            if not forzar and nombre in ultima and ahora - ultima[nombre] < intervalo:
                continue
            # Se marca antes de ejecutar: una tarea que falla no se reintenta cada minuto.
            ultima[nombre] = ahora
            logger.info("Scheduler: ejecutando tarea '%s'", nombre)
            funcion()
        except Exception:
            logger.exception("Scheduler: falló la tarea '%s'", nombre)


class Command(BaseCommand):
    help = 'Proceso en segundo plano que ejecuta periódicamente las tareas programadas (alertas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once', action='store_true',
            help='Ejecuta todas las tareas una vez y termina (para cron y pruebas)',
        )

    def handle(self, *args, **options):
        ultima = {}
        if options['once']:
            correr_tareas(ultima, time.monotonic(), forzar=True)
            self.stdout.write(self.style.SUCCESS('Tareas ejecutadas una vez.'))
            return

        self.stdout.write('Scheduler iniciado. Ctrl+C para detener.')
        try:
            while True:
                close_old_connections()
                correr_tareas(ultima, time.monotonic())
                time.sleep(PAUSA_SEGUNDOS)
        except KeyboardInterrupt:
            self.stdout.write('Scheduler detenido.')
