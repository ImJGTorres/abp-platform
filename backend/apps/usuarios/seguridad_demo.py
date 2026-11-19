from django.conf import settings
from django.core.management.base import CommandError


def exigir_entorno_de_desarrollo(options):
    """Los comandos seed_*_demo crean usuarios con contraseña fija: no corren con DEBUG=False
    (producción) salvo que se pase --forzar de forma explícita."""
    if not settings.DEBUG and not options.get('forzar'):
        raise CommandError(
            'Este comando crea usuarios con una contraseña conocida y solo corre con DEBUG=True. '
            'Usa --forzar si de verdad quieres ejecutarlo en este entorno.'
        )


def agregar_argumento_forzar(parser):
    parser.add_argument('--forzar', action='store_true', help='Permite ejecutarlo con DEBUG=False.')
